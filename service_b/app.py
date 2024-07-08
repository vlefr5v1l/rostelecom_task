from flask import Flask, request, jsonify
import re
import uuid
import pika
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

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
        port=DB_PORT,
        client_encoding='UTF8'
    )


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id UUID PRIMARY KEY,
            equipment_id VARCHAR(255) NOT NULL,
            parameters JSONB NOT NULL,
            status VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()


init_db()

# RabbitMQ configuration
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
            break
        except pika.exceptions.AMQPConnectionError:
            print("Failed to connect to RabbitMQ. Retrying in 5 seconds")
            time.sleep(5)


connect_to_rabbitmq()


@app.route('/api/v1/equipment/cpe/<string:id>', methods=['POST'])
def create_task(id):
    if not re.match(r'^[a-zA-Z0-9]{6,}$', id):
        return jsonify({"code": 404, "message": "The requested equipment is not found"}), 404
    data = request.json
    task_id = str(uuid.uuid4())

    task = {
        "id": task_id,
        "equipment_id": id,
        "parameters": json.dumps(data),
        "status": "pending"
    }
    logger.info(f"Task: {task}")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO tasks (id, equipment_id, parameters, status)
        VALUES (%s, %s, %s, %s)
    ''', (task['id'], task['equipment_id'], task['parameters'], task['status']))
    conn.commit()
    cur.close()
    conn.close()

    channel.basic_publish(exchange='',
                          routing_key='config_tasks',
                          body=json.dumps(task))

    logger.info(f"Task saved in database: {task}")

    return jsonify({"code": 200, "taskId": task_id}), 200


@app.route('/api/v1/equipment/cpe/<string:id>/task/<string:task>', methods=['GET'])
def get_task_status(id, task):
    if not re.match(r'^[a-zA-Z0-9]{6,}$', id):
        return jsonify({"code": 404, "message": "The requested equipment is not found"}), 404

    logger.info(f"task status start")

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM tasks WHERE id = %s', (task,))
    task = cur.fetchone()
    cur.close()
    conn.close()
    logger.info(f"task {task}")
    task_status=str(task['status']).lower()

    if not task_status:
        return jsonify({"code": 404, "message": "The requested task is not found"}), 404
    if task_status == 'completed':
        return jsonify({"code": 200, "message": "Completed"}), 200
    elif task_status in ['pending', 'running']:
        logger.info(f"МЫ ТУТ")
        return jsonify({"code": 204, "message": "Task is still running"}), 200
    else:
        return jsonify({"code": 500, "message": "Internal provisioning exception"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, ssl_context=('cert.pem', 'key.pem'))
