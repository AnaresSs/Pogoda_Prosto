from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.keyboards import kb_reply
from app.bot.states import Registration

router = Router()


@router.callback_query(F.data == 'editGeo')
async def callback_edit_geo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Registration.waiting_for_locality)
    await callback.message.answer(
        'Отправь геолокацию 📍 или напиши название населённого пункта 🏙️',
        reply_markup=kb_reply.get_keyboard_start(),
    )