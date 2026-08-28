#!/bin/bash
set -e

# Переходим в корень репозитория (скрипт лежит в scripts/)
cd "$(dirname "$0")/.."

echo "Запускаю загрузку городов в БД..."
docker compose -f docker/docker-compose.yml --project-directory . run --rm weather_bot python -m app.scripts.seed_cities "$@"

echo "Готово!"