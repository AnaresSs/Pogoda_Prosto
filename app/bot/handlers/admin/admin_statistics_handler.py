from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery

from app.bot.keyboards import kb_inline
from app.services import statistics_service

router = Router()


@router.callback_query(F.data == 'admin_stats')
async def callback_admin_stats(callback: CallbackQuery):
    stats = await statistics_service.get_statistics()

    total = stats['total']

    lines = [
        '📊 <b>Статистика</b>',
        '',
        '👥 <b>Пользователи:</b>',
        f'Всего: {total}',
        f'Новых за день: +{stats["new_today"]}',
        f'Новых за неделю: +{stats["new_week"]}',
        '',
        '🏙️ <b>Города:</b>',
    ]

    if total == 0:
        lines.append('Пока нет пользователей')
    else:
        for i, (name, count) in enumerate(stats['localities'], 1):
            percent = count / total * 100
            lines.append(f'{i}. {name} — {count} ({percent:.1f}%)')
        if stats['rest_count'] > 0:
            percent = stats['rest_count'] / total * 100
            lines.append(f'Прочие города — {stats["rest_count"]} ({percent:.1f}%)')

    await callback.message.edit_text(
        '\n'.join(lines),
        parse_mode=ParseMode.HTML,
        reply_markup=kb_inline.get_keyboard_admin_stats(),
    )