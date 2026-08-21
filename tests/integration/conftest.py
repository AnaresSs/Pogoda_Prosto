import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import decorators
from app.database.models import Base

TEST_DB_URL = "postgresql+asyncpg://test:test@localhost:5433/weather_test"


@pytest.fixture
async def db(monkeypatch):
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    maker = async_sessionmaker(engine)
    monkeypatch.setattr(decorators, "async_session", maker)

    yield maker

    await engine.dispose()
