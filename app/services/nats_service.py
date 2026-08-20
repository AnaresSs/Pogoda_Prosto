import json
from datetime import datetime

from nats.aio.client import Client
from nats.js import JetStreamContext

from app.core import nats_setup
from app.core.config import NATS_ADMIN_SENDER_CONSUMER

_nc: Client | None = None
_js: JetStreamContext | None = None


async def init():
    global _nc, _js
    nc, js = await nats_setup.setup()
    _nc, _js = nc, js


def get_js():
    if _js is None:
        raise RuntimeError("NATS service is not initialized")
    return _js


async def publish(subject: str, payload: bytes, msg_id: str):
    await get_js().publish(subject, payload, headers={"Nats-Msg-Id": msg_id})


async def subscribe(subject: str, durable: str):
    return await get_js().pull_subscribe(subject, durable=durable)


async def publish_weather_task(user_id: int, send_at: datetime):
    msg_id = f"weather:{user_id}:{send_at.date().isoformat()}"
    payload = json.dumps({"user_id": user_id, "send_at": send_at.isoformat()}).encode()
    await publish("weather.daily", payload, msg_id)


async def publish_admin_mailing(mailing_id: str, user_id: int, from_chat_id: int, message_id: int):
    subject = f"admin.mailing.{mailing_id}"
    msg_id = f"admin_mailing:{mailing_id}:{user_id}"
    payload = json.dumps({
        "type": "user",
        "user_id": user_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id,
    }).encode()
    await publish(subject, payload, msg_id)


async def publish_admin_mailing_summary(mailing_id: str, admin_chat_id: int, total: int):
    subject = f"admin.mailing.{mailing_id}"
    msg_id = f"admin_mailing_summary:{mailing_id}"
    payload = json.dumps({
        "type": "summary",
        "admin_chat_id": admin_chat_id,
        "total": total,
    }).encode()
    await publish(subject, payload, msg_id)


async def subscribe_admin_mailing():
    return await subscribe("admin.mailing.>", NATS_ADMIN_SENDER_CONSUMER)


async def close():
    global _nc
    if _nc is not None:
        await _nc.close()
        _nc = None
