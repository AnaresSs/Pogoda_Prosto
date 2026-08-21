#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "Синхронизируемся с репозиторием..."
# Жёсткое приведение к состоянию origin/main: сервер всегда зеркало репозитория.
# Локальные правки затираются намеренно (.env не трогается — он не в git)
git fetch origin
git reset --hard origin/main

echo "Пересобираем и перезапускаем контейнеры..."
docker compose up --build -d

echo "Ждём успешный старт бота (до 30 секунд)..."
STARTED=0
for i in $(seq 1 15); do
    if docker compose logs --tail 100 weather_bot 2>/dev/null | grep -q "Начало работы"; then
        STARTED=1
        break
    fi
    sleep 2
done

docker compose ps
docker compose logs --tail 20 weather_bot

if [ "$STARTED" -eq 1 ]; then
    echo "Бот запустился успешно"
else
    echo "Маркер 'Начало работы' не найден за 30 секунд — бот не поднялся, проверь логи вручную: docker compose logs weather_bot"
    exit 1
fi
