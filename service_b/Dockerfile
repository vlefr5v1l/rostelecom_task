FROM python:3.11

WORKDIR /service_b

COPY requirements.txt .
COPY cert.pem .
COPY key.pem .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5001

CMD ["python", "app.py"]