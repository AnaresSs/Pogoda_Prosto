import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database.models import Base

# Отдельная тестовая БД (порт 5433, контейнер из docker/docker-compose.test.yml) —
# продовые данные никогда не затрагиваются
TEST_DB_URL = "postgresql+asyncpg://test:test@localhost:5433/weather_test"


@pytest.fixture
async def db():
    # --- Подготовка: чистая схема перед каждым тестом ---
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Сессия передаётся в тесты ЯВНО — сервисы принимают её первым аргументом,
    # никакой подмены модулей (манкипатчинга) не требуется
    maker = async_sessionmaker(engine)
    async with maker() as session:
        yield session

    await engine.dispose()
