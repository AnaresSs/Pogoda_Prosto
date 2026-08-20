from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.keyboards import kb_inline
from app.services import tg_user_service

router = Router()


@router.callback_query(F.data == 'toggle_notifications')
async def callback_toggle_notifications(callback: CallbackQuery, state: FSMContext):
    user = await tg_user_service.get_user(callback.from_user.id)
    if user is None:
        return

    enabled = not user.notifications_enabled
    await tg_user_service.set_notifications(callback.from_user.id, enabled)

    message_text = 'Уведомления включены ✅' if enabled else 'Уведомления отключены ❌'

    await callback.answer(message_text)
    await callback.message.edit_text(
        '<b>Главное меню</b>',
        parse_mode=ParseMode.HTML,
        reply_markup=kb_inline.get_keyboard_menu(enabled),
    )