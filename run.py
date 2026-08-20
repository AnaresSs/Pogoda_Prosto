import asyncio
from aiogram import Bot, Dispatcher
from app.core.config import TOKEN
import aiohttp

from app.database import models
from app.core import globals
from app.services import nats_service
from app.tasks import weather_mailing_task
from app.tasks import admin_mailing_task
from app.bot.handlers.user import start_handler
from app.bot.handlers.user import weather_handler
from app.bot.handlers.user import geo_handler
from app.bot.handlers.user import notifications_handler
from app.bot.handlers.admin import admin_handler
from app.bot.handlers.admin import admin_statistics_handler
from app.bot.handlers.admin import admin_mailing_handler



bot = Bot(token=TOKEN)
dp = Dispatcher()

globals.bot = bot


async def main():
    await models.async_main()

    print('✅ База данных запущена')

    dp.include_routers(start_handler.router,
                   weather_handler.router,
                   geo_handler.router,
                   notifications_handler.router,
                   admin_handler.router,
                   admin_statistics_handler.router,
                   admin_mailing_handler.router)

    print('✅ Обработчики подключены')

    globals.aiohttp_session = aiohttp.ClientSession()

    print('✅ aiohttp подключен')

    await nats_service.init()

    print('✅ NATS подключен')

    worker = asyncio.create_task(weather_mailing_task.weather_mailing_worker())
    sender_worker = asyncio.create_task(weather_mailing_task.weather_sender_worker())
    admin_worker = asyncio.create_task(admin_mailing_task.admin_mailing_worker())

    print('✅ Воркеры погодной рассылки запущены')
    print('✅ Воркер админ-рассылки запущен')

    print('✅ Начало работы')

    try:
        await dp.start_polling(bot)
    finally:
        worker.cancel()
        sender_worker.cancel()
        admin_worker.cancel()
        await nats_service.close()
        await globals.aiohttp_session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')