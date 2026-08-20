from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_keyboard_start():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='📍 Отправить геолокацию', request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


