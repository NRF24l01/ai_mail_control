FROM python:3.11-slim

WORKDIR /app

COPY MailWorker/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy necessary files
COPY MailWorker /app/MailWorker
COPY config.py /app/config.py
COPY manage.py /app/manage.py
COPY RedisClient.py /app/RedisClient.py
COPY DBClient.py /app/DBClient.py
COPY models /app/models

ENV PYTHONPATH=/app

CMD ["python", "-m", "MailWorker.MailWorker"]
