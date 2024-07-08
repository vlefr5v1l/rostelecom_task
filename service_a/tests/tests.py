import unittest
from service_a.app import app


class AppTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_create_task_valid_data(self):
        response = self.app.post(
            '/api/v1/equipment/cpe/123456', json={
                "timeoutInSeconds": 14,
                "parameters": {
                    "username": "admin",
                    "password": "admin",
                    "vlan": 534,
                    "interfaces": [1, 2, 3, 4]
                }
            }, headers={'Content-Type': 'application/json'})

        self.assertEqual(response.status_code, 200)

    def test_create_task_invalid_id(self):
        response = self.app.post(
            '/api/v1/equipment/cpe/123', json={"param": "value"})
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()
