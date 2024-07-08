import json
import unittest
from unittest.mock import patch, MagicMock
from service_b.app import app


class AppTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('service_b.app.get_db_connection')
    def test_init_db(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        from service_b.app import init_db
        init_db()

        mock_cur.execute.assert_called()
        mock_conn.commit.assert_called()
        mock_cur.close.assert_called()
        mock_conn.close.assert_called()

    @patch('service_b.app.pika.BlockingConnection')
    def test_connect_to_rabbitmq(self, mock_blocking_connection):
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_blocking_connection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel

        from service_b.app import connect_to_rabbitmq
        connect_to_rabbitmq()

        mock_channel.queue_declare.assert_any_call(queue='config_tasks')
        mock_channel.queue_declare.assert_any_call(queue='config_results')

    @patch('service_b.app.channel.basic_publish')
    @patch('service_b.app.get_db_connection')
    def test_create_task_valid_data(self, mock_get_db_connection, mock_basic_publish):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_get_db_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        response = self.app.post(
            '/api/v1/equipment/cpe/123456', json={"param": "value"})

        self.assertEqual(response.status_code, 200)
        mock_basic_publish.assert_called()

    @patch('service_b.app.channel.basic_publish')
    @patch('service_b.app.get_db_connection')
    def test_create_task_invalid_id(self, mock_get_db_connection, mock_basic_publish):
        response = self.app.post(
            '/api/v1/equipment/cpe/123', json={"param": "value"})
        self.assertEqual(response.status_code, 404)

    @patch('service_b.app.get_db_connection')
    def test_get_task_status(self, mock_get_db_connection):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {"status": "completed"}
        mock_get_db_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur

        response = self.app.get('/api/v1/equipment/cpe/123456/task/12345678')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["message"], "Completed")


if __name__ == '__main__':
    unittest.main()
