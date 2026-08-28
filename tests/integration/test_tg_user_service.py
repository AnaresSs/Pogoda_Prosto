from app.database.models import TelegramUser
from app.services import locality_service, statistics_service, tg_user_service


# Хелпер: создаёт город и возвращает его id (нужен для FK у пользователей)
async def make_locality(session, name):
    await locality_service.add_locality(session, name, 55.7558, 37.6173, utc_offset=3)
    locality = await locality_service.get_locality(session, name)
    return locality.id


# Хелпер: кладёт пользователя напрямую в БД с заданным состоянием.
# В обход сервисов — чтобы тест проверял только то, что нужно,
# включая состояния, для которых сервисных функций нет
async def make_user(session, tg_id, notifications_enabled=True, locality_id=None):
    session.add(TelegramUser(
        id=tg_id,
        username=None,
        notifications_enabled=notifications_enabled,
        locality_id=locality_id,
    ))
    # flush отправляет INSERT в БД внутри транзакции, не завершая её:
    # данные видны запросам в этой же сессии
    await session.flush()


# Базовые операции получения пользователя
class TestAddAndCheckUser:
    async def test_add_and_get_user(self, db):
        # Созданный пользователь находится по tg_id
        await make_user(db, 1)

        user = await tg_user_service.get_user(db, 1)

        assert user is not None

    async def test_get_missing_user(self, db):
        # Несуществующий пользователь → None (важно для хэндлеров бота)
        assert await tg_user_service.get_user(db, 42) is None


# Фильтры get_users — на них строится выбор аудитории админ-рассылки
class TestGetUsersFilters:
    async def setup_users(self, session):
        # Три пользователя покрывают все комбинации флагов:
        # 1 — город + уведомления вкл; 2 — город + выкл; 3 — без города + вкл
        moscow_id = await make_locality(session, "Москва")
        spb_id = await make_locality(session, "Питер")
        await make_user(session, 1, notifications_enabled=True, locality_id=moscow_id)
        await make_user(session, 2, notifications_enabled=False, locality_id=spb_id)
        await make_user(session, 3, notifications_enabled=True, locality_id=None)

    async def test_all_users(self, db):
        # Без фильтров возвращаются все пользователи
        await self.setup_users(db)

        users = await tg_user_service.get_users(db)

        assert len(users) == 3

    async def test_filter_notifications_on(self, db):
        # Фильтр "уведомления включены" → только 1 и 3
        await self.setup_users(db)

        users = await tg_user_service.get_users(db, notifications_enabled=True)

        assert {u.id for u in users} == {1, 3}

    async def test_filter_notifications_off(self, db):
        # Фильтр "уведомления выключены" → только 2
        await self.setup_users(db)

        users = await tg_user_service.get_users(db, notifications_enabled=False)

        assert {u.id for u in users} == {2}

    async def test_filter_with_locality(self, db):
        # Фильтр "с городом" → 1 и 2 (регрессия бага с `is not None` вместо .is_not(None))
        await self.setup_users(db)

        users = await tg_user_service.get_users(db, has_locality=True)

        assert {u.id for u in users} == {1, 2}

    async def test_filter_without_locality(self, db):
        # Фильтр "без города" → только 3
        await self.setup_users(db)

        users = await tg_user_service.get_users(db, has_locality=False)

        assert {u.id for u in users} == {3}


# Смена города и переключение уведомлений
class TestEditLocality:
    async def test_edit_by_name_case_insensitive(self, db):
        # Город сохраняется независимо от регистра ввода ("москва" → Москва)
        moscow_id = await make_locality(db, "Москва")
        await make_user(db, 1)

        result = await tg_user_service.edit_locality(db, 1, "москва")

        assert result is True
        user = await tg_user_service.get_user(db, 1)
        assert user.locality_id == moscow_id

    async def test_edit_unknown_city_returns_false(self, db):
        # Несуществующий город → False, локация пользователя не меняется
        await make_user(db, 1)

        result = await tg_user_service.edit_locality(db, 1, "Атлантида")

        assert result is False

    async def test_set_notifications(self, db):
        # Выключение уведомлений реально сохраняется в БД
        await make_user(db, 1)

        await tg_user_service.set_notifications(db, 1, False)

        user = await tg_user_service.get_user(db, 1)
        assert user.notifications_enabled is False


# Регистрация нового пользователя через /start
class TestAddUserIfNotRegister:
    async def test_first_call_creates(self, db):
        # Первый вызов создаёт запись и сообщает об этом
        created = await tg_user_service.add_user_if_not_register(db, 7, "vasya")

        assert created is True
        assert await tg_user_service.get_user(db, 7) is not None

    async def test_second_call_skips(self, db):
        # Повторный /start не создаёт дубликат
        await tg_user_service.add_user_if_not_register(db, 7, "vasya")

        created = await tg_user_service.add_user_if_not_register(db, 7, "vasya")

        assert created is False


# Данные для /admin_stats
class TestStatistics:
    async def test_statistics_counts(self, db):
        # Итого 3 пользователя; топ городов — Москва с двумя пользователями;
        # пользователь без города не попадает в статистику городов
        moscow_id = await make_locality(db, "Москва")
        await make_user(db, 1, locality_id=moscow_id)
        await make_user(db, 2, locality_id=moscow_id)
        await make_user(db, 3, locality_id=None)

        stats = await statistics_service.get_statistics(db)

        assert stats["total"] == 3
        assert stats["new_today"] == 3  # все созданы сейчас → "новые за день"
        assert len(stats["localities"]) == 1
        name, count = stats["localities"][0]
        assert name == "Москва"
        assert count == 2
        assert stats["rest_count"] == 0
