from sqlalchemy import select, update, func

from app.database.models import Locality


class LocalityRepository:
    def __init__(self, session):
        self.session = session

    async def add_locality(self, name: str, latitude: float, longitude: float, utc_offset: int):
        self.session.add(Locality(name=name, latitude=latitude, longitude=longitude, utc_offset=utc_offset))

    async def is_locality(self, name: str):
        locality = await self.session.scalar(select(Locality).where(Locality.name == name))
        return locality is not None

    async def edit_locality(self, name: str, latitude: float, longitude: float, utc_offset: int):
        result = await self.session.execute(update(Locality)
                                            .where(Locality.name == name)
                                            .values(latitude=latitude, longitude=longitude, utc_offset=utc_offset))
        return result.rowcount > 0

    async def get_by_name(self, name: str): # lower() для отсутсвия строго учета регистра
        locality = await self.session.scalar(select(Locality).where(func.lower(Locality.name) == name.lower()))
        return locality

    async def get_by_id(self, locality_id: int):
        locality = await self.session.scalar(select(Locality).where(Locality.id == locality_id))
        return locality

    async def get_like(self, name: str):
        localities = await self.session.scalars(select(Locality).where(Locality.name.like(f'%{name}%')))
        return localities.all()

    async def get_in_bbox(self, lat_min: float, lat_max: float, lon_min: float, lon_max: float):
        localities = await self.session.scalars(select(Locality)
                                                .where(Locality.latitude.between(lat_min, lat_max),
                                                       Locality.longitude.between(lon_min, lon_max)))
        return localities.all()

    async def get_all(self):
        localities = await self.session.scalars(select(Locality))
        return localities.all()