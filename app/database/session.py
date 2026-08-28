from contextlib import asynccontextmanager

from app.database.models import async_session


@asynccontextmanager
async def session_scope():
    """Транзакция на единицу работы: коммит при успехе, откат при ошибке.

    Используется там, где нет aiogram-middleware: воркеры NATS, скрипты.
    В хэндлерах сессию открывает DbSessionMiddleware и коммитит один раз
    на весь апдейт.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
