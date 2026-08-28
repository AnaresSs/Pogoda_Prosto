#!/bin/bash
set -e

# Переходим в корень репозитория (скрипт лежит в scripts/)
cd "$(dirname "$0")/.."

COMPOSE="docker compose -f docker/docker-compose.yml --project-directory ."

echo "Синхронизируемся с репозиторием..."
# Жёсткое приведение к состоянию origin/main: сервер всегда зеркало репозитория.
# Локальные правки затираются намеренно (.env не трогается — он не в git)
git fetch origin
git reset --hard origin/main

echo "Пересобираем и перезапускаем контейнеры..."
$COMPOSE up --build -d

echo "Ждём успешный старт бота (до 30 секунд)..."
STARTED=0
for i in $(seq 1 15); do
    if $COMPOSE logs --tail 100 weather_bot 2>/dev/null | grep -q "Начало работы"; then
        STARTED=1
        break
    fi
    sleep 2
done

$COMPOSE ps
$COMPOSE logs --tail 20 weather_bot

if [ "$STARTED" -eq 1 ]; then
    echo "Бот запустился успешно"
else
    echo "Маркер 'Начало работы' не найден за 30 секунд — бот не поднялся, проверь логи вручную: $COMPOSE logs weather_bot"
    exit 1
fi
