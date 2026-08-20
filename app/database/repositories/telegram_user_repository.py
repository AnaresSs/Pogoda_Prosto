from sqlalchemy import select, update, func

from datetime import datetime

from app.database.models import TelegramUser, Locality


class TelegramUserRepository:
    def __init__(self, session):
        self.session = session

    async def add_user(self, tg_id: int, tg_username: str):
        self.session.add(TelegramUser(id=tg_id, username=tg_username))

    async def is_user(self, tg_id: int):
        user = await self.session.scalar(select(TelegramUser).where(TelegramUser.id == tg_id))
        return user is not None

    async def edit_user(self, tg_id: int, locality_id: int):
        result = await self.session.execute(update(TelegramUser)
                                            .where(TelegramUser.id == tg_id)
                                            .values(locality_id=locality_id))
        return result.rowcount > 0

    async def update_notifications(self, tg_id: int, enabled: bool):
        result = await self.session.execute(update(TelegramUser)
                                            .where(TelegramUser.id == tg_id)
                                            .values(notifications_enabled=enabled))
        return result.rowcount > 0

    async def get_users(self, has_locality: bool | None = None, notifications_enabled: bool | None = None):
        stmt = select(TelegramUser)
        if has_locality is not None:
            if has_locality:
                stmt = stmt.where(TelegramUser.locality_id is not None)
            else:
                stmt = stmt.where(TelegramUser.locality_id is None)
        if notifications_enabled is not None:
            stmt = stmt.where(TelegramUser.notifications_enabled == notifications_enabled)
        users = await self.session.scalars(stmt)
        return users.all()

    async def get_users_after_date(self, after_date: datetime):
        users = await self.session.scalars(select(TelegramUser).where(TelegramUser.created_at > after_date))
        return users.all()

    async def get_user(self, tg_id: int):
        user = await self.session.scalar(select(TelegramUser).where(TelegramUser.id == tg_id))
        return user

    async def get_count(self):
        count = await self.session.scalar(select(func.count(TelegramUser.id)))
        return count or 0

    async def get_count_after_date(self, after_date: datetime):
        count = await self.session.scalar(select(func.count(TelegramUser.id))
                                          .where(TelegramUser.created_at > after_date))
        return count or 0

    async def get_locality_stats(self):
        rows = await self.session.execute(
            select(Locality.name, func.count(TelegramUser.id))
            .join(Locality, TelegramUser.locality_id == Locality.id)
            .where(TelegramUser.locality_id is not None)
            .group_by(Locality.id, Locality.name)
            .order_by(func.count(TelegramUser.id).desc())
        )
        return rows.all()




