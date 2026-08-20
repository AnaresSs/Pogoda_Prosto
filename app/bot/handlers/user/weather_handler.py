from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery

from app.bot.keyboards import kb_inline
from app.bot.notifications import weather_message
from app.integrations.weather_client import weather_client
from app.services import locality_service
from app.services import tg_user_service

router = Router()


async def get_user_weather(tg_id: int, days: int):
    user = await tg_user_service.get_user(tg_id)
    if user is None or user.locality_id is None:
        return None
    locality = await locality_service.get_by_id(user.locality_id)
    if locality is None:
        return None
    return await weather_client.get_forecast(locality.latitude, locality.longitude, days=days)


async def send_forecast(callback: CallbackQuery, days: int):
    weather = await get_user_weather(callback.from_user.id, days)
    if weather is None:
        await callback.answer('Сначала укажи свой город 📍', show_alert=True)
        return

    if days == 1:
        text = weather_message.format_weather_message(weather)
    else:
        text = weather_message.format_weather_forecast(weather)

    await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb_inline.get_keyboard_weather())


@router.callback_query(F.data == 'weather_now')
async def callback_weather_now(callback: CallbackQuery):
    await send_forecast(callback, 1)


@router.callback_query(F.data == 'weather_days_3')
async def callback_weather_days_3(callback: CallbackQuery):
    await send_forecast(callback, 3)


@router.callback_query(F.data == 'weather_days_7')
async def callback_weather_days_7(callback: CallbackQuery):
    await send_forecast(callback, 7)


@router.callback_query(F.data == 'weather_days_14')
async def callback_weather_days_14(callback: CallbackQuery):
    await send_forecast(callback, 14)