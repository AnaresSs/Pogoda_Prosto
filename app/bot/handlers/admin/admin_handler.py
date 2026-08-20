from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.bot.keyboards import kb_inline
from app.core.config import ADMIN_IDS

router = Router()


@router.message(Command('admin'))
async def command_admin(message: Message, state: FSMContext):
    await state.clear()

    if message.from_user.id not in ADMIN_IDS:
        return

    await message.answer('Открыто меню администратора', reply_markup=kb_inline.get_keyboard_admin())


@router.callback_query(F.data == 'returnToAdminMenu')
async def callback_return_to_admin_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text('Открыто меню администратора', reply_markup=kb_inline.get_keyboard_admin())