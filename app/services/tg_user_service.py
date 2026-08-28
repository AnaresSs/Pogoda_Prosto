from app.database.repositories.telegram_user_repository import TelegramUserRepository

from app.services import locality_service


async def add_user_if_not_register(session, tg_id: int, tg_username: str):
    tg_repo = TelegramUserRepository(session)
    if not await tg_repo.is_user(tg_id):
        await tg_repo.add_user(tg_id, tg_username)
        return True
    return False


async def edit_locality(session, tg_id: int, name: str):
    tg_repo = TelegramUserRepository(session)
    locality = await locality_service.get_locality(session, name)
    if locality is not None:
        return await tg_repo.edit_user(tg_id, locality.id)
    return False


async def edit_locality_by_coords(session, tg_id: int, latitude: float, longitude: float):
    locality = await locality_service.get_nearest(session, latitude, longitude)
    if locality is None:
        return None
    tg_repo = TelegramUserRepository(session)
    if await tg_repo.edit_user(tg_id, locality.id):
        return locality
    return None


async def get_users(session, has_locality: bool | None = None, notifications_enabled: bool | None = None):
    tg_repo = TelegramUserRepository(session)

    return await tg_repo.get_users(has_locality=has_locality, notifications_enabled=notifications_enabled)


async def get_user(session, tg_id: int):
    tg_repo = TelegramUserRepository(session)

    return await tg_repo.get_user(tg_id)


async def set_notifications(session, tg_id: int, enabled: bool):
    tg_repo = TelegramUserRepository(session)

    return await tg_repo.update_notifications(tg_id, enabled)
