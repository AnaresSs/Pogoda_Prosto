from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

router = Router()


from app.services import tg_user_service
from app.bot.keyboards import kb_inline, kb_reply
from app.bot.states import Registration


async def get_menu_keyboard(tg_id):
    user = await tg_user_service.get_user(tg_id)
    notifications_enabled = user.notifications_enabled if user is not None else True
    return kb_inline.get_keyboard_menu(notifications_enabled)


@router.message(CommandStart())
async def command_start(message: Message, state: FSMContext):
    await state.clear()

    tg_id = message.from_user.id
    username = message.from_user.username
    if await tg_user_service.add_user_if_not_register(tg_id, username):
        await state.set_state(Registration.waiting_for_locality)
        await message.answer('''
<b>👋 Привет!</b> Добро пожаловать в мой погодный бот! 🌤️

<b>🌀 Обо мне:</b> Каждое утро я присылаю тебе прогноз погоды на день, чтобы ты был готов к любому сюрпризу природы. ☔❄️☀️

<b>📋 Что я умею:</b>
🌤️ Прогноз на сегодня
📅 Прогноз на 3/7/14 дней
📍 Сменить регион

<b>📍 Регистрация:</b>
Чтобы я подбирал точные данные, мне нужно знать, где ты находишься.
Отправь геолокацию 📍 или напиши название населённого пункта в России (город, посёлок, село) 🏙️

<b>🚀 Погнали!</b> После этого я всё настрою и начнём!
''', parse_mode=ParseMode.HTML, reply_markup=kb_reply.get_keyboard_start())
    else:
        menu = await get_menu_keyboard(tg_id)
        await message.answer('''
<b>👋 Привет!</b> Добро пожаловать в мой погодный бот! 🌤️

<b>🌀 Обо мне:</b> Каждое утро я присылаю тебе прогноз погоды на день, чтобы ты был готов к любому сюрпризу природы. ☔❄️☀️

<b>📋 Что я умею:</b>
🌤️ Прогноз на сегодня
📅 Прогноз на 3/7/14 дней
📍 Сменить регион
''', parse_mode=ParseMode.HTML, reply_markup=menu)


@router.message(F.location)
async def location_handler(message: Message, state: FSMContext):
    latitude = message.location.latitude
    longitude = message.location.longitude

    locality = await tg_user_service.edit_locality_by_coords(message.from_user.id, latitude, longitude)

    if locality is not None:
        await state.clear()
        await message.answer(f'''
📍 <b>{locality.name}</b> — нашёл твой населённый пункт!
Сохранён по координатам: {latitude:.4f}, {longitude:.4f}

Всё готово! Погода будет ждать тебя каждое утро. 🌤️
''', parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())
        menu = await get_menu_keyboard(message.from_user.id)
        await message.answer('<b>Главное меню</b>', reply_markup=menu, parse_mode=ParseMode.HTML)
    else:
        await message.answer('''
😕 Рядом с тобой не нашлось населённого пункта.
Попробуй написать название города текстом 📝.''',
reply_markup=ReplyKeyboardRemove())


@router.message(Registration.waiting_for_locality)
async def message_location(message: Message, state: FSMContext):
    tg_id = message.from_user.id

    if await tg_user_service.edit_locality(tg_id, message.text.strip()):
        await state.clear()
        await message.answer(f'''
✅ <b>{message.text.strip()}</b> — сохранил как твой населённый пункт!

Всё готово! Погода будет ждать тебя каждое утро. 🌤️
''', parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())
        menu = await get_menu_keyboard(tg_id)
        await message.answer('<b>Главное меню</b>', reply_markup=menu, parse_mode=ParseMode.HTML)
    else:
        await message.answer('''
😕 Такой населённый пункт не найден.
Проверь написание и попробуй ещё раз.
''', reply_markup=ReplyKeyboardRemove())



@router.callback_query(F.data == 'returnToMenu')
async def callback_return_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    menu = await get_menu_keyboard(callback.from_user.id)
    try:
        await callback.message.edit_text('<b>Главное меню</b>', reply_markup=menu,
                                         parse_mode=ParseMode.HTML)
    except:
        await callback.message.delete()
        await callback.message.answer('<b>Главное меню</b>', reply_markup=menu,
                                      parse_mode=ParseMode.HTML)

