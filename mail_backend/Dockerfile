FROM python:3.11-slim

WORKDIR /app

COPY mail_backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY models /app/models
COPY mail_backend/app.py /app/app.py
COPY mail_backend/requirements.txt /app/requirements.txt
COPY mail_backend/entrypoint.sh /app/entrypoint.sh

COPY .. /app

ENV PYTHONPATH=/app

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
