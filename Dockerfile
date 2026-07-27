FROM python:3.12.8-slim

# Trust Zscaler (or similar) during pip on corporate networks.
COPY docker/certs/zscaler-root-ca.pem /usr/local/share/ca-certificates/zscaler-root-ca.crt
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV BACKUP_DIR=/backups \
    CONFIG_DIR=/config \
    WEB_PORT=8080

EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${WEB_PORT}"]
