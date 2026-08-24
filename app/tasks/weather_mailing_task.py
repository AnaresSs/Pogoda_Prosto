import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta

from nats.errors import TimeoutError

from app.bot.notifications.weather_mailing_notification import WeatherNotifier
from app.core.config import NATS_SENDER_CONSUMER, SEND_HOUR
from app.database.session import session_scope
from app.integrations.weather_client import WeatherClient
from app.services import locality_service
from app.services import nats_service
from app.services import tg_user_service

logger = logging.getLogger(__name__)

SENDER_SUBJECT = "weather.daily"
last_checked_minute = None


async def publish_due_users(session, utc_now):
    localities = {locality.id: locality for locality in await locality_service.get_all(session)}
    users = await tg_user_service.get_users(session)

    published = 0
    for user in users:
        if not user.notifications_enabled or user.locality_id is None:
            continue
        locality = localities.get(user.locality_id)
        if locality is None:
            continue

        local_time = utc_now + timedelta(hours=locality.utc_offset)
        if local_time.hour != SEND_HOUR or local_time.minute != 0:
            continue

        await nats_service.publish_weather_task(user.id, local_time)
        published += 1

    if published:
        logger.info("опубликовано задач рассылки: %d", published)


async def weather_mailing_worker():
    global last_checked_minute
    while True:
        utc_now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        if utc_now.minute != last_checked_minute:
            try:
                async with session_scope() as session:
                    await publish_due_users(session, utc_now)
                last_checked_minute = utc_now.minute
            except Exception as exc:
                logger.error("Ошибка рассылки: %s", exc)
                await asyncio.sleep(10)
                continue
        await asyncio.sleep(1)


async def handle_weather_message(session, weather_client: WeatherClient,
                                 notifier: WeatherNotifier, message):
    data = json.loads(message.data.decode())
    user_id = data["user_id"]

    user = await tg_user_service.get_user(session, user_id)
    if user is None or not user.notifications_enabled or user.locality_id is None:
        return

    locality = await locality_service.get_by_id(session, user.locality_id)
    if locality is None:
        return

    weather = await weather_client.get_forecast(locality.latitude, locality.longitude)
    await notifier.send_daily(user_id, weather, locality.name)


async def weather_sender_worker(weather_client: WeatherClient, notifier: WeatherNotifier):
    sub = await nats_service.subscribe(SENDER_SUBJECT, NATS_SENDER_CONSUMER)
    while True:
        try:
            messages = await sub.fetch(10, timeout=1)
        except (TimeoutError, asyncio.TimeoutError):
            continue
        except Exception as exc:
            logger.error("Ошибка fetch в погодном воркере: %r", exc)
            await asyncio.sleep(2)
            continue
        for message in messages:
            try:
                # Транзакция на сообщение: коммит БД -> ack
                async with session_scope() as session:
                    await handle_weather_message(session, weather_client, notifier, message)
                await message.ack()
            except Exception as exc:
                logger.error("Ошибка обработки задачи: %r", exc)
                try:
                    await message.nak()
                except Exception:
                    pass


