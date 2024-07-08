FROM python:3.11

WORKDIR /app

COPY requirements.txt .
COPY cert.pem .
COPY key.pem .

RUN pip install --no-cache-dir -r requirements.txt

COPY .. .

EXPOSE 5001

CMD ["python", "service_a.app.py", "service_b.app.py", "worker.worker.py"]