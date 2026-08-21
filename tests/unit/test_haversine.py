from app.services.locality_service import haversine

MOSCOW = (55.7558, 37.6173)
SPB = (59.9343, 30.3351)
VLADIVOSTOK = (43.1155, 131.8855)


def test_same_point_is_zero():
    assert haversine(*MOSCOW, *MOSCOW) == 0


def test_moscow_to_spb_about_630_km():
    distance = haversine(*MOSCOW, *SPB)
    assert 620 <= distance <= 650


def test_distance_across_country_is_large():
    distance = haversine(*MOSCOW, *VLADIVOSTOK)
    assert distance > 6000


def test_distance_is_symmetric():
    assert haversine(*MOSCOW, *SPB) == haversine(*SPB, *MOSCOW)
