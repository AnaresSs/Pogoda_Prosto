from app.services import locality_service
from app.database.repositories.locality_repository import LocalityRepository


# Хелпер: добавляет город через сервис (данные видны в той же сессии)
async def make_locality(session, name="Москва", lat=55.7558, lon=37.6173):
    await locality_service.add_locality(session, name, lat, lon, utc_offset=3)


# Поиск города по названию — то, что вызывается при вводе "москва" текстом
class TestGetByName:
    async def test_found_exact_case(self, db):
        # Точное совпадение регистра находит город
        await make_locality(db, "Москва")

        locality = await locality_service.get_locality(db, "Москва")

        assert locality is not None
        assert locality.name == "Москва"

    async def test_found_ignoring_case(self, db):
        # Смешанный регистр ("мОскВа") тоже находит — работает func.lower в запросе
        await make_locality(db, "Москва")

        locality = await locality_service.get_locality(db, "мОскВа")

        assert locality is not None

    async def test_not_found(self, db):
        # Несуществующий город → None, а не исключение
        await make_locality(db, "Москва")

        locality = await locality_service.get_locality(db, "Париж")

        assert locality is None


# Подбор ближайшего города по геолокации пользователя
class TestGetNearest:
    async def test_finds_nearest_within_radius(self, db):
        # Из двух городов в радиусе 75 км выбирается ближайший
        await make_locality(db, "Деревня", lat=55.80, lon=37.60)
        await make_locality(db, "Город", lat=55.90, lon=37.70)

        nearest = await locality_service.get_nearest(db, 55.81, 37.61)

        assert nearest is not None
        assert nearest.name == "Деревня"

    async def test_nothing_within_radius(self, db):
        # Единственный город далеко за радиусом → None
        await make_locality(db, "Далеко", lat=50.0, lon=30.0)

        nearest = await locality_service.get_nearest(db, 55.75, 37.61)

        assert nearest is None


# Прямая проверка методов репозитория
class TestRepository:
    async def test_get_by_id(self, db):
        # Город находится по первичному ключу
        await make_locality(db, "Самара")

        all_localities = await LocalityRepository(db).get_all()

        found = await locality_service.get_by_id(db, all_localities[0].id)

        assert found is not None
        assert found.name == "Самара"

    async def test_get_by_id_missing(self, db):
        # Несуществующий id → None
        found = await locality_service.get_by_id(db, 9999)

        assert found is None
