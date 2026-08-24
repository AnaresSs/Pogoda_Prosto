from aiogram import Bot
from aiogram.enums import ParseMode

from app.bot.notifications.weather_message import format_weather_message


class WeatherNotifier:
    """Отправка погодных уведомлений.

    Бот привязывается один раз в конструкторе (создаётся в run.py
    и передаётся воркеру явно) — никаких обращений к глобальному состоянию.
    """

    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_daily(self, tg_id: int, weather, city_name: str = ""):
        await self.bot.send_message(
            tg_id,
            format_weather_message(weather, city_name),
            parse_mode=ParseMode.HTML,
        )
