#!/bin/sh
# Миграции
echo "Running migrations"
python models/migrate.py

# Запуск backend
exec uvicorn mail_backend.app:app --host 0.0.0.0 --port 8000


