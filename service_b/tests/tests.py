import pytest
import json
from unittest.mock import patch, MagicMock
from ..app import app, get_db_connection

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_db_connection():
    with patch('app.get_db_connection') as mock:
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        mock.return_value = conn
        yield mock

def test_create_task_valid_id(client, mock_db_connection):
    response = client.post('/api/v1/equipment/cpe/abc123', json={
        'timeoutInSeconds': 60,
        'parameters': {'key': 'value'}
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'taskId' in data

def test_create_task_invalid_id(client):
    response = client.post('/api/v1/equipment/cpe/abc', json={
        'timeoutInSeconds': 60,
        'parameters': {'key': 'value'}
    })
    assert response.status_code == 404

def test_create_task_missing_data(client):
    response = client.post('/api/v1/equipment/cpe/abc123', json={})
    assert response.status_code == 500

@pytest.mark.parametrize("status,expected_code,expected_message", [
    ('completed', 200, 'Completed'),
    ('pending', 204, 'Task is still running'),
    ('running', 204, 'Task is still running'),
    ('failed', 500, 'Task failed'),
])
def test_get_task_status(client, mock_db_connection, status, expected_code, expected_message):
    cur = mock_db_connection.return_value.cursor.return_value
    cur.fetchone.return_value = {'status': status}

    response = client.get('/api/v1/equipment/cpe/abc123/task/task-id-123')
    assert response.status_code == expected_code
    if expected_code != 204:
        data = json.loads(response.data)
        assert data['message'] == expected_message

def test_get_task_status_not_found(client, mock_db_connection):
    cur = mock_db_connection.return_value.cursor.return_value
    cur.fetchone.return_value = None

    response = client.get('/api/v1/equipment/cpe/abc123/task/task-id-123')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['message'] == 'The requested task is not found'

def test_get_task_status_invalid_id(client):
    response = client.get('/api/v1/equipment/cpe/abc/task/task-id-123')
    assert response.status_code == 404