from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from app.bot.keyboards import kb_inline
from app.bot.notifications.weather_message import weather_message
from app.integrations.weather_client import WeatherClient
from app.services import locality_service
from app.services import tg_user_service

router = Router()


async def get_user_weather(session, weather_client: WeatherClient, tg_id: int, days: int):
    user = await tg_user_service.get_user(session, tg_id)
    if user is None or user.locality_id is None:
        return None
    locality = await locality_service.get_by_id(session, user.locality_id)
    if locality is None:
        return None
    weather = await weather_client.get_forecast(locality.latitude, locality.longitude, days=days)
    return weather, locality.name


async def send_forecast(session, weather_client: WeatherClient, callback: CallbackQuery, days: int):
    result = await get_user_weather(session, weather_client, callback.from_user.id, days)
    if result is None:
        await callback.answer('Сначала укажи свой город 📍', show_alert=True)
        return

    weather, city_name = result

    if days == 1:
        text = weather_message.format_weather_message(weather, city_name)
    else:
        text = weather_message.format_weather_forecast(weather, city_name)

    try:
        await callback.message.edit_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=kb_inline.get_keyboard_weather(days),
        )
        await callback.answer()
    except TelegramBadRequest:
        # Telegram отклоняет редактирование, если текст не изменился —
        # для кнопки «Обновить» это штатная ситуация «данные актуальны»
        await callback.answer('Данные уже актуальны ✅')


@router.callback_query(F.data == 'weather_now')
async def callback_weather_now(callback: CallbackQuery, session, weather_client: WeatherClient):
    await send_forecast(session, weather_client, callback, 1)


@router.callback_query(F.data.startswith('weather_refresh_'))
async def callback_weather_refresh(callback: CallbackQuery, session, weather_client: WeatherClient):
    days = int(callback.data.rsplit('_', 1)[1])
    await send_forecast(session, weather_client, callback, days)


@router.callback_query(F.data == 'weather_days_3')
async def callback_weather_days_3(callback: CallbackQuery, session, weather_client: WeatherClient):
    await send_forecast(session, weather_client, callback, 3)


@router.callback_query(F.data == 'weather_days_7')
async def callback_weather_days_7(callback: CallbackQuery, session, weather_client: WeatherClient):
    await send_forecast(session, weather_client, callback, 7)


@router.callback_query(F.data == 'weather_days_14')
async def callback_weather_days_14(callback: CallbackQuery, session, weather_client: WeatherClient):
    await send_forecast(session, weather_client, callback, 14)