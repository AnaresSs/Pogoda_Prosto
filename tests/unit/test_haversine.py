from app.services.locality_service import haversine

# Реальные координаты городов для проверки формулы
MOSCOW = (55.7558, 37.6173)
SPB = (59.9343, 30.3351)
VLADIVOSTOK = (43.1155, 131.8855)


def test_same_point_is_zero():
    # Расстояние точки до самой себя — ноль
    assert haversine(*MOSCOW, *MOSCOW) == 0


def test_moscow_to_spb_about_630_km():
    # Известное расстояние Москва—Питер ≈ 630 км; допуск ±20 км на погрешность формулы
    distance = haversine(*MOSCOW, *SPB)
    assert 620 <= distance <= 650


def test_distance_across_country_is_large():
    # Москва—Владивосток через всю страну — больше 6000 км
    distance = haversine(*MOSCOW, *VLADIVOSTOK)
    assert distance > 6000


def test_distance_is_symmetric():
    # Формула симметрична: A→B равно B→A (важно для поиска ближайшего города)
    assert haversine(*MOSCOW, *SPB) == haversine(*SPB, *MOSCOW)
