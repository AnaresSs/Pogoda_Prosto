#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "Запускаю загрузку городов в БД..."
docker compose run --rm weather_bot python -m app.scripts.seed_cities "$@"

echo "Готово!"