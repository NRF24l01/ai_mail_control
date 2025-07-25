FROM python:3.11-slim

COPY migrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY . /app
COPY models /app/models

COPY migrator/run_migrations.sh .
RUN chmod +x run_migrations.sh

ENV PYTHONPATH=/app
