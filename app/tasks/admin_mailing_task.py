import asyncio
import json
import logging

from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError
from nats.errors import TimeoutError

from app.core import globals
from app.services import nats_service

logger = logging.getLogger(__name__)

MAX_DELIVER = 3

results = {}


def increment(subject: str, key: str):
    stats = results.setdefault(subject, {"success": 0, "blocked": 0, "errors": 0})
    stats[key] += 1


async def handle_admin_mailing_message(message):
    data = json.loads(message.data.decode())

    if data.get("type") == "summary":
        stats = results.pop(message.subject, {"success": 0, "blocked": 0, "errors": 0})
        lines = [
            '📨 <b>Рассылка завершена</b>',
            '',
            f'Всего пользователей: {data["total"]}',
            f'✅ Отправлено: {stats["success"]}',
            f'🚫 Заблокировали бота: {stats["blocked"]}',
            f'⚠️ Ошибки: {stats["errors"]}',
        ]
        logger.info("summary для %s: %s", message.subject, stats)
        await globals.bot.send_message(
            data["admin_chat_id"],
            '\n'.join(lines),
            parse_mode=ParseMode.HTML,
        )
        await message.ack()
        return

    try:
        await globals.bot.copy_message(
            chat_id=data["user_id"],
            from_chat_id=data["from_chat_id"],
            message_id=data["message_id"],
        )
        increment(message.subject, "success")
        await message.ack()
        logger.info("отправлено пользователю %s", data['user_id'])
    except TelegramForbiddenError:
        increment(message.subject, "blocked")
        await message.term()
        logger.warning("пользователь %s заблокировал бота", data['user_id'])
    except Exception as exc:
        logger.error("ошибка доставки %s: %s", data['user_id'], exc)
        if message.metadata.num_delivered >= MAX_DELIVER:
            increment(message.subject, "errors")
            await message.term()
        else:
            await message.nak()


async def admin_mailing_worker():
    sub = await nats_service.subscribe_admin_mailing()
    while True:
        try:
            messages = await sub.fetch(10, timeout=1)
        except (TimeoutError, asyncio.TimeoutError):
            continue
        except Exception as exc:
            logger.error("Ошибка fetch в админ-воркере: %r", exc)
            await asyncio.sleep(2)
            continue
        for message in messages:
            try:
                await handle_admin_mailing_message(message)
            except Exception as exc:
                logger.error("Ошибка обработки рассылки: %s", exc)
                try:
                    await message.nak()
                except Exception:
                    pass


