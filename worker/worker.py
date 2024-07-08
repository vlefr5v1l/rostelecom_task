import pika
import requests
import json
import psycopg2
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

rabbitmq_host = 'rabbitmq'
connection = None
channel = None


def connect_to_rabbitmq():
    global connection, channel
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
            channel = connection.channel()
            channel.queue_declare(queue='config_tasks')
            channel.queue_declare(queue='config_results')
            print("Connected to RabbitMQ")
            break
        except pika.exceptions.AMQPConnectionError:
            print("Failed to connect to RabbitMQ. Retrying in 5 seconds...")
            time.sleep(5)


connect_to_rabbitmq()


DB_NAME = "postgresql"
DB_USER = "user"
DB_PASS = "password"
DB_HOST = "postgres"
DB_PORT = "5432"


def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT
    )


def callback(ch, method, properties, body):
    logger.info(f"Received message: {body}")

    try:
        task = json.loads(body)
        task_id = task.get("id")
        parameters = task.get("parameters")
        device_id = task.get("equipment_id")
        logger.info(f"device_id: {device_id}")
        logger.info(f"Received parameters: {parameters}")
        try:
            logger.info('start response')
            response = requests.post(f'https://service-a:5000/api/v1/equipment/cpe/{device_id}',
                                     headers={'Content-Type': 'application/json'},
                                     json=parameters,
                                     verify=False,
                                     timeout=61)
            logger.info(f"response: {response.status_code}")
            if response.status_code == 200:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('''
                    UPDATE tasks
                    SET status = %s
                    WHERE id = %s
                ''', ('completed', task_id))
                conn.commit()
                cur.close()
                conn.close()

                channel.basic_publish(
                    exchange='',
                    routing_key='config_results',
                    body=json.dumps({"task_id": task_id, "status": "completed"})
                )
            else:
                channel.basic_publish(
                    exchange='',
                    routing_key='config_results',
                    body=json.dumps({"task_id": task_id, "status": "failed"})
                )
        except requests.RequestException as e:
            print(f"Error calling service A: {str(e)}")
            channel.basic_publish(
                exchange='',
                routing_key='config_results',
                body=json.dumps({"task_id": task_id, "status": "failed"})
            )

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")


channel.basic_consume(queue='config_tasks', on_message_callback=callback, auto_ack=True)
print('Waiting for configuration tasks. To exit press CTRL+C')
channel.start_consuming()
