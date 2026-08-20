from aiogram.enums import ParseMode

from app.bot.notifications.weather_message import format_weather_message
from app.core import globals


async def send_weather_notification(tg_id: int, weather):
    bot = globals.bot
    if bot is None:
        raise RuntimeError("Bot is not initialized")

    await bot.send_message(tg_id, format_weather_message(weather), parse_mode=ParseMode.HTML)