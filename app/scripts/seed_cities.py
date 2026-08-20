import asyncio
import os
import sys
import urllib.request
import zipfile

from sqlalchemy import delete, func, select

from app.database.models import Locality, TelegramUser, async_session

BASE_URL = "https://download.geonames.org/export/dump"
MAIN_ZIP = "RU.zip"
ALT_ZIP = "alternatenames/RU.zip"
TXT_FILE = "RU.txt"
MIN_POPULATION = int(os.getenv("MIN_POPULATION", "1000"))
FORCE = "--force" in sys.argv


def download(url: str, dest: str) -> str:
    if os.path.exists(dest):
        print(f"Файл уже есть: {dest}")
        return dest
    print(f"Скачиваю {url} ...")
    urllib.request.urlretrieve(url, dest)
    return dest


def parse_main(path: str) -> dict:
    places = {}
    with zipfile.ZipFile(path) as zf:
        with zf.open(TXT_FILE) as f:
            for raw in f:
                parts = raw.decode("utf-8").rstrip("\n").split("\t")
                if len(parts) < 18 or parts[6] != "P":
                    continue
                population = int(parts[14]) if parts[14].strip() else 0
                if population < MIN_POPULATION:
                    continue
                places[parts[0]] = {
                    "name": parts[1],
                    "latitude": float(parts[4]),
                    "longitude": float(parts[5]),
                    "timezone": parts[17],
                }
    print(f"Населенных пунктов с населением >= {MIN_POPULATION}: {len(places)}")
    return places


def parse_alt_names(path: str) -> dict:
    russian = {}
    with zipfile.ZipFile(path) as zf:
        with zf.open(TXT_FILE) as f:
            for raw in f:
                parts = raw.decode("utf-8").rstrip("\n").split("\t")
                if len(parts) < 5:
                    continue
                geoname_id, lang, alt_name, is_preferred = parts[1], parts[2], parts[3], parts[4]
                if lang != "ru" or not alt_name.strip():
                    continue
                current = russian.get(geoname_id)
                if current is None or (is_preferred == "1" and current[1] != "1"):
                    russian[geoname_id] = (alt_name, is_preferred)
    print(f"Русских названий в файле: {len(russian)}")
    return russian


def build_rows(places: dict, russian: dict) -> list:
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    now = datetime.now(timezone.utc)
    rows = []
    missing_tz = 0
    for geoname_id, p in places.items():
        alt = russian.get(geoname_id)
        name = alt[0] if alt else p["name"]

        try:
            offset = ZoneInfo(p["timezone"]).utcoffset(now)
            utc_offset = int(offset.total_seconds() // 3600)
        except Exception:
            missing_tz += 1
            utc_offset = 0

        rows.append({
            "name": name,
            "latitude": p["latitude"],
            "longitude": p["longitude"],
            "utc_offset": utc_offset,
        })
    if missing_tz:
        print(f"Не удалось определить таймзону для {missing_tz} записей (поставлено 0)")
    return rows


async def seed_db(rows: list):
    async with async_session() as session:
        current_count = await session.scalar(select(func.count(Locality.id))) or 0

        if current_count > 0:
            if not FORCE:
                print(f"В таблице localities уже {current_count} записей. Останавливаюсь (запусти с --force чтобы перезалить).")
                return
            user_count = await session.scalar(select(func.count(TelegramUser.id))) or 0
            if user_count > 0:
                print(f"Нельзя очистить localities: на неё ссылаются {user_count} пользователей.")
                return
            await session.execute(delete(Locality))
            print(f"Старые записи ({current_count}) удалены.")

        async with session.begin():
            for i in range(0, len(rows), 2000):
                batch = rows[i:i + 2000]
                session.add_all([Locality(**item) for item in batch])
                print(f"Загружено {min(i + 2000, len(rows))} из {len(rows)}")

    print("Готово! Города загружены в БД.")


async def main():
    cache_dir = os.getenv("GEONAMES_CACHE", "/tmp/geonames")
    os.makedirs(cache_dir, exist_ok=True)

    main_zip = download(f"{BASE_URL}/{MAIN_ZIP}", os.path.join(cache_dir, MAIN_ZIP))
    alt_zip = download(f"{BASE_URL}/{ALT_ZIP}", os.path.join(cache_dir, "alt_" + MAIN_ZIP))

    places = parse_main(main_zip)
    russian = parse_alt_names(alt_zip)
    rows = build_rows(places, russian)

    await seed_db(rows)


if __name__ == "__main__":
    asyncio.run(main())