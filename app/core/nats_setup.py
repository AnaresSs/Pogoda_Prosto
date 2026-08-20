import nats
from nats.aio.client import Client
from nats.js import JetStreamContext
from nats.js.api import (
    AckPolicy,
    ConsumerConfig,
    DeliverPolicy,
    RetentionPolicy,
    StorageType,
    StreamConfig,
)
from nats.js.errors import NotFoundError

from app.core.config import (
    NATS_ADMIN_SENDER_CONSUMER,
    NATS_ADMIN_STREAM_NAME,
    NATS_ADMIN_STREAM_SUBJECTS,
    NATS_SENDER_CONSUMER,
    NATS_STREAM_NAME,
    NATS_STREAM_SUBJECTS,
    NATS_URL,
)


async def connect():
    nc = await nats.connect(NATS_URL, max_reconnect_attempts=-1, reconnect_time_wait=2)
    return nc, nc.jetstream()


async def ensure_stream(js: JetStreamContext, name: str, subjects: list[str]):
    cfg = StreamConfig(
        name=name,
        subjects=subjects,
        storage=StorageType.FILE,
        retention=RetentionPolicy.LIMITS,
        max_age=100 * 60 * 60,
        duplicate_window=26 * 60 * 60,
    )
    try:
        await js.stream_info(name)
        await js.update_stream(cfg)
    except NotFoundError:
        await js.add_stream(cfg)


async def ensure_consumer(js: JetStreamContext, stream: str, durable: str, filter_subject: str):
    cfg = ConsumerConfig(
        durable_name=durable,
        ack_policy=AckPolicy.EXPLICIT,
        ack_wait=5 * 60,
        max_deliver=3,
        deliver_policy=DeliverPolicy.ALL,
        filter_subject=filter_subject,
    )
    try:
        await js.consumer_info(stream, durable)
    except NotFoundError:
        await js.add_consumer(stream, cfg)


async def setup():
    nc, js = await connect()
    await ensure_stream(js, NATS_STREAM_NAME, NATS_STREAM_SUBJECTS)
    await ensure_consumer(js, NATS_STREAM_NAME, NATS_SENDER_CONSUMER, "weather.>")
    await ensure_stream(js, NATS_ADMIN_STREAM_NAME, NATS_ADMIN_STREAM_SUBJECTS)
    await ensure_consumer(js, NATS_ADMIN_STREAM_NAME, NATS_ADMIN_SENDER_CONSUMER, "admin.mailing.>")
    return nc, js
