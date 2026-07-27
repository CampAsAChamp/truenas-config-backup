FROM python:3.12.8-slim

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV BACKUP_DIR=/backups \
    CONFIG_DIR=/config \
    WEB_PORT=8080

EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${WEB_PORT}"]
