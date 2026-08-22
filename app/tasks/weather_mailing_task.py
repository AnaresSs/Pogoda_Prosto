import asyncio
import json
from datetime import datetime, timezone, timedelta

from nats.errors import TimeoutError

from app.bot.notifications import weather_mailing_notification
from app.core.config import NATS_SENDER_CONSUMER, SEND_HOUR
from app.integrations.weather_client import weather_client
from app.services import locality_service
from app.services import nats_service
from app.services import tg_user_service

SENDER_SUBJECT = "weather.daily"
last_checked_minute = None


async def publish_due_users(utc_now):
    localities = {locality.id: locality for locality in await locality_service.get_all()}
    users = await tg_user_service.get_users()

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
        print(f"[publisher] опубликовано задач рассылки: {published}")


async def weather_mailing_worker():
    global last_checked_minute
    while True:
        utc_now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        if utc_now.minute != last_checked_minute:
            try:
                await publish_due_users(utc_now)
                last_checked_minute = utc_now.minute
            except Exception as exc:
                print(f"Ошибка рассылки: {exc}")
                await asyncio.sleep(10)
                continue
        await asyncio.sleep(1)


async def handle_weather_message(message):
    data = json.loads(message.data.decode())
    user_id = data["user_id"]

    user = await tg_user_service.get_user(user_id)
    if user is None or not user.notifications_enabled or user.locality_id is None:
        await message.ack()
        return

    locality = await locality_service.get_by_id(user.locality_id)
    if locality is None:
        await message.ack()
        return

    weather = await weather_client.get_forecast(locality.latitude, locality.longitude)
    await weather_mailing_notification.send_weather_notification(user_id, weather, locality.name)
    await message.ack()


async def weather_sender_worker():
    sub = await nats_service.subscribe(SENDER_SUBJECT, NATS_SENDER_CONSUMER)
    while True:
        try:
            messages = await sub.fetch(10, timeout=1)
        except (TimeoutError, asyncio.TimeoutError):
            continue
        except Exception as exc:
            print(f"Ошибка fetch в погодном воркере: {exc!r}")
            await asyncio.sleep(2)
            continue
        for message in messages:
            try:
                await handle_weather_message(message)
            except Exception as exc:
                print(f"Ошибка обработки задачи: {exc!r}")
                try:
                    await message.nak()
                except Exception:
                    pass


