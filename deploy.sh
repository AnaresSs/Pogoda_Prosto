#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "Потягиваем код из git..."
git pull

echo "Пересобираем и перезапускаем контейнеры..."
docker compose up --build -d

echo "Готово! Логи бота:"
docker compose logs -f weather_bot