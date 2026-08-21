import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import decorators
from app.database.models import Base

# Отдельная тестовая БД (порт 5433, контейнер из docker-compose.test.yml) —
# продовые данные никогда не затрагиваются
TEST_DB_URL = "postgresql+asyncpg://test:test@localhost:5433/weather_test"


@pytest.fixture
async def db(monkeypatch):
    # --- Подготовка: чистая схема перед каждым тестом ---
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    maker = async_sessionmaker(engine)

    # Подменяем фабрику сессий В ДЕКОРАТОРАХ (with_session / with_session_transaction).
    # Теперь любой вызов сервиса идёт не в продовую БД из .env, а в тестовую.
    monkeypatch.setattr(decorators, "async_session", maker)

    yield maker  # здесь выполняется тест

    # --- Разборка: движок закрывается после теста ---
    await engine.dispose()
