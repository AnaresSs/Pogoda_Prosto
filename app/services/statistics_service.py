from datetime import datetime, timezone, timedelta

from app.database.repositories.telegram_user_repository import TelegramUserRepository


async def get_statistics(session, top_localities: int = 10):
    tg_repo = TelegramUserRepository(session)
    now = datetime.now(timezone.utc)

    total = await tg_repo.get_count()
    new_today = await tg_repo.get_count_after_date(now - timedelta(days=1))
    new_week = await tg_repo.get_count_after_date(now - timedelta(days=7))

    locality_rows = await tg_repo.get_locality_stats()
    top = locality_rows[:top_localities]
    rest_count = sum(count for _, count in locality_rows[top_localities:])

    return {
        "total": total,
        "new_today": new_today,
        "new_week": new_week,
        "localities": top,
        "rest_count": rest_count,
    }
