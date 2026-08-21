from app.database.models import TelegramUser
from app.database.repositories.locality_repository import LocalityRepository
from app.services import locality_service, statistics_service, tg_user_service


async def make_locality(db, name):
    await locality_service.add_locality(name, 55.7558, 37.6173, utc_offset=3)
    async with db() as session:
        repo = LocalityRepository(session)
        locality = await repo.get_by_name(name)
        return locality.id


async def make_user(db, tg_id, notifications_enabled=True, locality_id=None):
    async with db() as session:
        session.add(TelegramUser(
            id=tg_id,
            username=None,
            notifications_enabled=notifications_enabled,
            locality_id=locality_id,
        ))
        await session.commit()


class TestAddAndCheckUser:
    async def test_add_and_get_user(self, db):
        await make_user(db, 1)

        user = await tg_user_service.get_user(1)

        assert user is not None

    async def test_get_missing_user(self, db):
        assert await tg_user_service.get_user(42) is None


class TestGetUsersFilters:
    async def setup_users(self, db):
        moscow_id = await make_locality(db, "Москва")
        spb_id = await make_locality(db, "Питер")
        await make_user(db, 1, notifications_enabled=True, locality_id=moscow_id)
        await make_user(db, 2, notifications_enabled=False, locality_id=spb_id)
        await make_user(db, 3, notifications_enabled=True, locality_id=None)

    async def test_all_users(self, db):
        await self.setup_users(db)

        users = await tg_user_service.get_users()

        assert len(users) == 3

    async def test_filter_notifications_on(self, db):
        await self.setup_users(db)

        users = await tg_user_service.get_users(notifications_enabled=True)

        assert {u.id for u in users} == {1, 3}

    async def test_filter_notifications_off(self, db):
        await self.setup_users(db)

        users = await tg_user_service.get_users(notifications_enabled=False)

        assert {u.id for u in users} == {2}

    async def test_filter_with_locality(self, db):
        await self.setup_users(db)

        users = await tg_user_service.get_users(has_locality=True)

        assert {u.id for u in users} == {1, 2}

    async def test_filter_without_locality(self, db):
        await self.setup_users(db)

        users = await tg_user_service.get_users(has_locality=False)

        assert {u.id for u in users} == {3}


class TestEditLocality:
    async def test_edit_by_name_case_insensitive(self, db):
        moscow_id = await make_locality(db, "Москва")
        await make_user(db, 1)

        result = await tg_user_service.edit_locality(1, "москва")

        assert result is True
        user = await tg_user_service.get_user(1)
        assert user.locality_id == moscow_id

    async def test_edit_unknown_city_returns_false(self, db):
        await make_user(db, 1)

        result = await tg_user_service.edit_locality(1, "Атлантида")

        assert result is False

    async def test_set_notifications(self, db):
        await make_user(db, 1)

        await tg_user_service.set_notifications(1, False)

        user = await tg_user_service.get_user(1)
        assert user.notifications_enabled is False


class TestAddUserIfNotRegister:
    async def test_first_call_creates(self, db):
        created = await tg_user_service.add_user_if_not_register(7, "vasya")

        assert created is True
        assert await tg_user_service.get_user(7) is not None

    async def test_second_call_skips(self, db):
        await tg_user_service.add_user_if_not_register(7, "vasya")

        created = await tg_user_service.add_user_if_not_register(7, "vasya")

        assert created is False


class TestStatistics:
    async def test_statistics_counts(self, db):
        moscow_id = await make_locality(db, "Москва")
        await make_user(db, 1, locality_id=moscow_id)
        await make_user(db, 2, locality_id=moscow_id)
        await make_user(db, 3, locality_id=None)

        stats = await statistics_service.get_statistics()

        assert stats["total"] == 3
        assert stats["new_today"] == 3
        assert len(stats["localities"]) == 1
        name, count = stats["localities"][0]
        assert name == "Москва"
        assert count == 2
        assert stats["rest_count"] == 0
