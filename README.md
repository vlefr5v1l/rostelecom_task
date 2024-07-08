# Тестовое задание Ростелеком

## Описание

Этот проект реализует два сервиса для предоставления асинхронного интерфейса инициирования задач на активацию оборудования. Проект включает:

1. **Сервис-заглушка A** — синхронный сервис конфигурации, предоставляющий HTTP/S endpoint для конфигурации конкретного устройства.
2. **Frontend сервис B** — асинхронный сервис, который создает задачи конфигурации и предоставляет endpoint для проверки статуса задач.

## Требования

- Python 2.7+
- RabbitMQ (или любой другой брокер сообщений)
- Поддержка HTTPS

## Структура проекта

```plaintext
project-root/
│
├── service_a/
│   ├──tests/
│   │   └── tests.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └──  app.py
│   
│
├── service_b/
│   ├──tests/
│   │   └── tests.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
│   
│
├── worker/
│   ├── worker.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── docker-compose.yml
└── README.md
```


## Запуск
```bash
git clone https://github.com/yourusername/yourproject.git
docker-compose up --build
```
## Конфигурация

## Service A (Сервис-заглушка)
### Endpoint: POST /api/v1/equipment/cpe/{id}

#### Пример запроса:
```json
{
  "timeoutInSeconds": 14,
  "parameters": [
    {"username": "admin"},
    {"password": "admin"},
    {"vlan": 534},
    {"interfaces": [1, 2, 3, 4]}
  ]
}
```
#### Пример ответа:
```json
{
  "code": 200,
  "message": "success"
}
```
#### Возможные ошибки:
```json
{
  "code": 500,
  "message": "Internal provisioning exception"
}
```
```json
{
  "code": 404,
  "message": "The requested equipment is not found"
}
```
## Service B
### Создание задачи
Endpoint: POST /api/v1/equipment/cpe/{id}

Пример ответа:

```json
{
  "code": 200,
  "taskId": "unique_task_id"
}
```
### Получение статуса задачи
Endpoint: GET /api/v1/equipment/cpe/{id}/task/{task}

#### Пример ответа:

```json
{
  "code": 200,
  "message": "Completed"
}
```
```json
{
  "code": 204,
  "message": "Task is still running"
}
```
#### Возможные ошибки:

```json
{
  "code": 500,
  "message": "Internal provisioning exception"
}
```
```json
{
  "code": 404,
  "message": "The requested equipment is not found"
}
```
```json
{
  "code": 404,
  "message": "The requested task is not found"
}
```

## Тестирование
Для запуска тестов выполните команду:

```bash
docker-compose exec service_a 
cd tests
pytest tests.py
```
```bash
docker-compose exec service_b
cd tests
pytest tests.py
```


## Диаграмма взаимодействия сервисов
![image](https://github.com/vlefr5v1l/rostelecom_task/assets/144193090/bf5b35b9-9401-40cd-9d5e-3be73b06d24a)

