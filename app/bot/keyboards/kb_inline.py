from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.core.config import SUPPORT_USERNAME


def get_keyboard_menu(notifications_enabled: bool = True):
    keyboard = InlineKeyboardBuilder()

    keyboard.button(text='Погода сегодня', callback_data='weather_now')
    keyboard.button(text='Погода на 3 дня', callback_data='weather_days_3')
    keyboard.button(text='Погода на неделю', callback_data='weather_days_7')
    keyboard.button(text='Погода на две недели', callback_data='weather_days_14')
    keyboard.button(text='Сменить геолокацию', callback_data='editGeo')

    if notifications_enabled:
        keyboard.button(text='🟢 Уведомления включены', callback_data='toggle_notifications')
    else:
        keyboard.button(text='🔴 Уведомления отключены', callback_data='toggle_notifications')

    if SUPPORT_USERNAME:
        keyboard.button(text='🆘 Поддержка', url=f'https://t.me/{SUPPORT_USERNAME}')

    keyboard.adjust(2, 2, 1, 1, 1)

    return keyboard.as_markup()


def get_keyboard_admin():
    keyboard = InlineKeyboardBuilder()

    keyboard.button(text='📊 Статистика', callback_data='admin_stats')
    keyboard.button(text='📨 Рассылка', callback_data='admin_mailing')
    keyboard.button(text='Вернуться в меню пользователя', callback_data='returnToMenu')

    keyboard.adjust(2, 1)

    return keyboard.as_markup()


def get_keyboard_admin_stats():
    keyboard = InlineKeyboardBuilder()

    keyboard.button(text='◀️ Назад', callback_data='returnToAdminMenu')

    return keyboard.as_markup()


def get_keyboard_mailing_message():
    keyboard = InlineKeyboardBuilder()

    keyboard.button(text='◀️ Назад', callback_data='mailing_back')

    return keyboard.as_markup()


def get_keyboard_mailing_audience():
    keyboard = InlineKeyboardBuilder()

    keyboard.button(text='👥 Все пользователи', callback_data='mailing_audience_all')
    keyboard.button(text='🏙️ С городом', callback_data='mailing_audience_with_city')
    keyboard.button(text='🚫 Без города', callback_data='mailing_audience_without_city')
    keyboard.button(text='📨 С ежедневной рассылкой', callback_data='mailing_audience_notif_on')
    keyboard.button(text='🔕 Без ежедневной рассылки', callback_data='mailing_audience_notif_off')
    keyboard.button(text='◀️ Назад', callback_data='mailing_back')

    keyboard.adjust(1, 1, 1, 1, 1, 1)

    return keyboard.as_markup()


def get_keyboard_weather(days: int = 1):
    keyboard = InlineKeyboardBuilder()

    keyboard.button(text='🔄 Обновить', callback_data=f'weather_refresh_{days}')
    keyboard.button(text='◀️ Назад в меню', callback_data='returnToMenu')

    keyboard.adjust(2)

    return keyboard.as_markup()

