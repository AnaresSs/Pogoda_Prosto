import time

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import kb_inline
from app.bot.states import Mailing
from app.core.config import ADMIN_IDS
from app.services import nats_service
from app.services import tg_user_service

router = Router()

AUDIENCE_FILTERS = {
    'mailing_audience_all': (None, None),
    'mailing_audience_with_city': (True, None),
    'mailing_audience_without_city': (False, None),
    'mailing_audience_notif_on': (None, True),
    'mailing_audience_notif_off': (None, False),
}


@router.callback_query(F.data == 'admin_mailing')
async def callback_admin_mailing(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return

    await state.set_state(Mailing.waiting_for_message)
    await callback.message.edit_text('''
Отправь сообщение для рассылки 📨
Оно будет скопировано всем выбранным пользователям.
''', reply_markup=kb_inline.get_keyboard_mailing_message())


@router.message(Mailing.waiting_for_message)
async def message_mailing_message(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    await state.update_data(from_chat_id=message.chat.id, message_id=message.message_id)
    await state.set_state(Mailing.waiting_for_audience)
    await message.answer('Теперь выбери аудиторию рассылки:', reply_markup=kb_inline.get_keyboard_mailing_audience())


@router.callback_query(Mailing.waiting_for_audience, F.data.startswith('mailing_audience_'))
async def callback_mailing_audience(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return

    await callback.answer()

    data = await state.get_data()
    has_locality, notifications_enabled = AUDIENCE_FILTERS[callback.data]

    users = await tg_user_service.get_users(
        has_locality=has_locality,
        notifications_enabled=notifications_enabled,
    )

    total = len(users)
    if total == 0:
        await state.clear()
        await callback.message.answer('По выбранным критериям пользователей не найдено 🙅')
        return

    mailing_id = str(time.time_ns())
    for user in users:
        await nats_service.publish_admin_mailing(
            mailing_id,
            user.id,
            data['from_chat_id'],
            data['message_id'],
        )
    await nats_service.publish_admin_mailing_summary(mailing_id, callback.from_user.id, total)

    await state.clear()
    await callback.message.answer(f'''
Рассылка запущена ✅
Всего пользователей: {total}
Сообщение будет скопировано каждому.
''')


@router.callback_query(F.data == 'mailing_back')
async def callback_mailing_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text('Открыто меню администратора', reply_markup=kb_inline.get_keyboard_admin())