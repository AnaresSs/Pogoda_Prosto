# 🌀 Погода Просто

Telegram-бот с прогнозами погоды и ежедневной рассылкой. Работает на данных [Open-Meteo](https://open-meteo.com/) (без API-ключа) и городах из открытой базы [GeoNames](https://www.geonames.org/).

## Возможности

**Для пользователей**
- 🌤 Прогноз на сегодня, 3, 7 и 14 дней
- 📍 Выбор города по названию (без учёта регистра) или по геолокации — подбирается ближайший населённый пункт в радиусе 75 км
- ⏰ Ежедневная рассылка строго в **07:00 локального времени** каждого города
- 🔔 Переключатель уведомлений

**Для администратора**
- 📊 Статистика: всего пользователей, новые за день/неделю, топ городов
- 📨 Рассылка любым сообщением (текст, фото, видео) с выбором аудитории:
  все / с городом / без города / с рассылкой вкл / выкл
- Отчёт о результате: доставлено, заблокировали бота, ошибки

## Технологии

| Слой | Технология |
|---|---|
| Бот | Python 3.12, [aiogram 3](https://docs.aiogram.dev/) |
| БД | PostgreSQL 16, SQLAlchemy 2 (asyncio) + asyncpg |
| Очередь задач | [NATS JetStream](https://nats.io/) |
| Погода | [Open-Meteo API](https://open-meteo.com/en/docs) |
| Города | GeoNames (`RU.zip` + `alternatenames`, ≥1000 жителей) |
| Тесты | pytest, pytest-asyncio (54 теста) |
| CI/CD | GitHub Actions → Docker Compose на сервере |

## Архитектура

```mermaid
flowchart TD
    U["👤 Пользователь Telegram"] <-->|"апдейты / сообщения"| B["aiogram handlers"]
    B --> S["services<br/>бизнес-логика"]
    S --> R["repositories"]
    R --> DB[("PostgreSQL")]

    S -->|"publish задач"| NS{{"NATS JetStream"}}
    NS -->|"pull, at-least-once"| W1["publisher<br/>проверка времени каждую минуту"]
    W1 -->|"weather.daily"| NS
    NS --> W2["sender<br/>погода пользователю"]
    NS --> W3["admin worker<br/>админ-рассылка"]
    W2 --> WM["Open-Meteo API"]
```

*Хэндлеры принимают апдейты, сервисы содержат бизнес-логику, репозитории ходят в PostgreSQL. Долгие операции (рассылки) уходят через NATS JetStream в фоновые воркеры: publisher кладёт задачи, sender и admin worker разбирают очередь с гарантией at-least-once.*

### Как устроена ежедневная рассылка

Пайплайн разделён на два независимых этапа через NATS JetStream:

1. **Publisher** каждую минуту проверяет: не наступил ли `SEND_HOUR:00` локального времени чьего-то города. Для попавших под окно пользователей публикует задачу `weather.daily`.
2. **Sender** забирает задачи из очереди (pull-подписка, durable consumer), запрашивает погоду у Open-Meteo и отправляет сообщение пользователю. Только после успешной отправки задача подтверждается (`ack`).

Такая схема даёт **at-least-once гарантию**: если бот упал посреди рассылки, неподтверждённые задачи доедут после рестарта. Каждая задача несёт уникальный `Nats-Msg-Id` — NATS сам отбрасывает дубликаты в пределах окна дедупликации.

Устойчивость к сбоям:
- Open-Meteo вернул 5xx или rate limit → до 3 повторов с растущей паузой
- Задача провалилась → `nak` и возврат в очередь (до 3 доставок)
- Пользователь заблокировал бота → задача закрывается, попадает в отчёт как «🚫»

Админская рассылка построена так же: одна задача на пользователя + финальное summary-сообщение с итогами.

## Структура проекта

```
app/
├── bot/
│   ├── handlers/
│   │   ├── user/            # старт, погода, геолокация, уведомления
│   │   └── admin/           # меню, статистика, рассылка
│   ├── keyboards/           # inline/reply клавиатуры
│   ├── middlewares/         # DbSessionMiddleware: сессия БД на апдейт
│   ├── notifications/       # форматтеры текстов погоды
│   └── states.py            # FSM-состояния (регистрация, рассылка)
├── core/
│   ├── config.py            # переменные окружения
│   └── nats_setup.py        # стримы и консьюмеры JetStream
├── database/
│   ├── models.py            # ORM-модели: TelegramUser, Locality
│   ├── repositories/        # запросы к БД
│   ├── session.py           # session_scope: транзакция на единицу работы
│   └── ...
├── integrations/
│   └── weather_client.py    # клиент Open-Meteo с ретраями
├── scripts/
│   └── seed_cities.py       # загрузка городов из GeoNames
├── services/                # бизнес-логика между хэндлерами и БД
└── tasks/                   # воркеры NATS (погодный и админский)

tests/
├── unit/                    # форматтеры, геометрия (haversine)
└── integration/             # сервисы и репозитории против PostgreSQL
.github/workflows/ci.yml     # CI: тесты → автодеплой
scripts/
├── deploy.sh                # обновление и перезапуск на сервере
└── seed_cities.sh           # запуск сид-скрипта в контейнере
docker/
├── Dockerfile
├── docker-compose.yml       # postgres + nats + weather_bot
└── docker-compose.test.yml  # PostgreSQL для локальных тестов
```

## Быстрый старт

Нужны установленные [Docker](https://docs.docker.com/engine/install/) и git.

```bash
git clone https://github.com/AnaresSs/Pogoda_Prosto.git
cd Pogoda_Prosto

# создать .env по шаблону и заполнить значениями
cp .env.example .env
nano .env

# поднять postgres, nats и бота
docker compose -f docker/docker-compose.yml --project-directory . up -d --build

# загрузить ~4800 городов России в базу (скачивает архивы GeoNames, ~15 МБ)
./scripts/seed_cities.sh
```

Готово — бот отвечает в Telegram. Логи: `docker compose -f docker/docker-compose.yml --project-directory . logs -f weather_bot`.

## Переменные окружения

| Переменная | Описание | Пример |
|---|---|---|
| `TOKEN` | токен бота от [@BotFather](https://t.me/BotFather) | `1234567890:AAExK9mQrTz4vBnW8yLpCdF2gHsJaN6uVwXo` |
| `SQLALCHEMY_URL` | строка подключения к БД | `postgresql+asyncpg://user:pass@localhost:5432/db` |
| `SUPER_ADMIN_ID` | Telegram ID администратора | `123456789` |
| `ADMIN_GROUP_ID` | ID админ-группы для уведомлений | `-1009876543210` |
| `SERVER_IP` | IP сервера (для инфо-сообщений) | `203.0.113.10` |
| `NATS_URL` | адрес NATS | `nats://localhost:4222` |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | реквизиты контейнера БД | `weather_db` |
| `SEND_HOUR` | час рассылки, необязательно (по умолчанию `7`) | `10` |

## Тесты

Юнит-тесты проверяют чистую логику (форматтеры погоды, расчёт расстояний), интеграционные гоняют сервисы и репозитории на настоящем PostgreSQL — отдельном контейнере на порту 5433, продовая база не затрагивается.

```bash
pip install -r requirements-dev.txt
docker compose -f docker/docker-compose.test.yml up -d
pytest
```

Тесты дважды ловили реальные баги до продакшена — например, неработающие фильтры аудитории рассылки.

## CI/CD

Пуш в `main` запускает конвейер GitHub Actions:

1. **test** — подъём Postgres-контейнера, установка зависимостей, `pytest`. Красный крест = деплой отменяется
2. **deploy** — SSH на сервер (ключи в зашифрованных Secrets репозитория): синхронизация кода через `git reset --hard origin/main`, пересборка контейнеров, ожидание маркера успешного старта в логах бота

Ручной деплой с самого сервера: `./scripts/deploy.sh`.
