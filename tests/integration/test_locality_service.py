from app.services import locality_service
from app.database.repositories.locality_repository import LocalityRepository


# Хелпер: добавляет город напрямую через сервис (транзакция коммитится декоратором)
async def make_locality(name="Москва", lat=55.7558, lon=37.6173):
    await locality_service.add_locality(name, lat, lon, utc_offset=3)


# Поиск города по названию — то, что вызывается при вводе "москва" текстом
class TestGetByName:
    async def test_found_exact_case(self, db):
        # Точное совпадение регистра находит город
        await make_locality("Москва")

        locality = await locality_service.get_locality("Москва")

        assert locality is not None
        assert locality.name == "Москва"

    async def test_found_ignoring_case(self, db):
        # Смешанный регистр ("мОскВа") тоже находит — работает func.lower в запросе
        await make_locality("Москва")

        locality = await locality_service.get_locality("мОскВа")

        assert locality is not None

    async def test_not_found(self, db):
        # Несуществующий город → None, а не исключение
        await make_locality("Москва")

        locality = await locality_service.get_locality("Париж")

        assert locality is None


# Подбор ближайшего города по геолокации пользователя
class TestGetNearest:
    async def test_finds_nearest_within_radius(self, db):
        # Из двух городов в радиусе 75 км выбирается ближайший
        await make_locality("Деревня", lat=55.80, lon=37.60)
        await make_locality("Город", lat=55.90, lon=37.70)

        nearest = await locality_service.get_nearest(55.81, 37.61)

        assert nearest is not None
        assert nearest.name == "Деревня"

    async def test_nothing_within_radius(self, db):
        # Единственный город далеко за радиусом → None
        await make_locality("Далеко", lat=50.0, lon=30.0)

        nearest = await locality_service.get_nearest(55.75, 37.61)

        assert nearest is None


# Прямая проверка методов репозитория
class TestRepository:
    async def test_get_by_id(self, db):
        # Город находится по первичному ключу
        await make_locality("Самара")

        async with db() as session:
            repo = LocalityRepository(session)
            all_localities = await repo.get_all()

        found = await locality_service.get_by_id(all_localities[0].id)

        assert found is not None
        assert found.name == "Самара"

    async def test_get_by_id_missing(self, db):
        # Несуществующий id → None
        found = await locality_service.get_by_id(9999)

        assert found is None
