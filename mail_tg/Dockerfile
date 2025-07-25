FROM python:3.11-slim

WORKDIR /app

COPY mail_tg/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy necessary files
COPY mail_tg /app/mail_tg
COPY config.py /app/config.py
COPY manage.py /app/manage.py
COPY DBClient.py /app/DBClient.py
COPY RedisClient.py /app/RedisClient.py
COPY models /app/models

ENV PYTHONPATH=/app

CMD ["python", "-m", "mail_tg.bot"]
