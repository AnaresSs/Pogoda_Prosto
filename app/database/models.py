from app.core.config import SQLALCHEMY_URL

from sqlalchemy import BigInteger, ForeignKey, Integer, String, DateTime, Boolean, Float, Text
from sqlalchemy.orm import DeclarativeBase, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

from datetime import datetime, timedelta, timezone

engine = create_async_engine(url=SQLALCHEMY_URL)

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass



class TelegramUser(Base):
    __tablename__ = 'telegram_users'

    id = mapped_column(BigInteger, primary_key=True)
    username = mapped_column(String)
    notifications_enabled = mapped_column(Boolean, default=True)
    locality_id = mapped_column(Integer, ForeignKey('localities.id'), nullable=True, default=None)
    created_at = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    locality_r = relationship('Locality', back_populates='users_r')


class Locality(Base):
    __tablename__ = 'localities'

    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String)
    latitude = mapped_column(Float)
    longitude = mapped_column(Float)
    utc_offset = mapped_column(Integer)

    users_r = relationship('TelegramUser', back_populates='locality_r')





async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

