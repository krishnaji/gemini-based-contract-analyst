FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt

RUN  pip install --no-ache-dir -r requirements.txt

COPY ..

CMD exec gunicorn --bind:8080 --workers 1 app:app