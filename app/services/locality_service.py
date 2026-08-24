from app.core.config import GEO_SEARCH_DELTA_DEGREES, GEO_SEARCH_RADIUS_KM
from app.database.decorators import with_session, with_session_transaction
from app.database.repositories.locality_repository import LocalityRepository

import math

EARTH_RADIUS_KM = 6371.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


@with_session_transaction
async def add_locality(session, name: str, latitude: float, longitude: float, utc_offset: int):
    locality_repo = LocalityRepository(session)
    await locality_repo.add_locality(name, latitude, longitude, utc_offset)


@with_session
async def get_all(session):
    locality_repo = LocalityRepository(session)
    return await locality_repo.get_all()


@with_session
async def get_locality(session, name: str):
    locality_repo = LocalityRepository(session)
    return await locality_repo.get_by_name(name)


@with_session
async def get_by_id(session, locality_id: int):
    locality_repo = LocalityRepository(session)
    return await locality_repo.get_by_id(locality_id)


@with_session
async def get_nearest(session, latitude: float, longitude: float,
                      delta: float = GEO_SEARCH_DELTA_DEGREES,
                      radius_km: float = GEO_SEARCH_RADIUS_KM):
    locality_repo = LocalityRepository(session)
    candidates = await locality_repo.get_in_bbox(
        latitude - delta, latitude + delta,
        longitude - delta, longitude + delta,
    )

    nearest = None
    nearest_distance = None
    for locality in candidates:
        distance = haversine(latitude, longitude, locality.latitude, locality.longitude)
        if distance <= radius_km and (nearest_distance is None or distance < nearest_distance):
            nearest = locality
            nearest_distance = distance
    return nearest






