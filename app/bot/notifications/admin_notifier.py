from aiogram import Bot
from aiogram.enums import ParseMode


class AdminNotifier:
    """Сообщения администратору: итоги рассылок и прочие отчёты."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_mailing_summary(self, chat_id: int, total: int, stats: dict):
        lines = [
            '📨 <b>Рассылка завершена</b>',
            '',
            f'Всего пользователей: {total}',
            f'✅ Отправлено: {stats["success"]}',
            f'🚫 Заблокировали бота: {stats["blocked"]}',
            f'⚠️ Ошибки: {stats["errors"]}',
        ]
        await self.bot.send_message(chat_id, '\n'.join(lines), parse_mode=ParseMode.HTML)
