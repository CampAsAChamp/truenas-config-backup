FROM python:3.12.8-slim

# Optional Zscaler (or similar) CA for pip on corporate networks (gitignored; see README).
COPY docker/certs/ /tmp/certs/
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && if [ -f /tmp/certs/zscaler-root-ca.pem ]; then \
         cp /tmp/certs/zscaler-root-ca.pem /usr/local/share/ca-certificates/zscaler-root-ca.crt \
         && update-ca-certificates; \
       fi \
    && rm -rf /var/lib/apt/lists/* /tmp/certs

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV BACKUP_DIR=/backups \
    CONFIG_DIR=/config \
    WEB_PORT=8080

EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${WEB_PORT}"]
