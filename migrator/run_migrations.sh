#!/bin/sh
set -e

cd models

# Проверка наличия файлов в папке миграций
if [ ! -d "./migrations" ] || [ -z "$(ls -A ./migrations)" ]; then
    echo ">> Aerich init..."
    aerich init -t tortoise_config.TORTOISE_ORM
    aerich init-db || true
fi

echo ">> Running aerich migrate..."
aerich migrate || true

echo ">> Running aerich upgrade..."
aerich upgrade

echo ">> Migration complete"
