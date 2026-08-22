import asyncio

from aiohttp import ClientResponseError

from app.core import globals


class WeatherClient:
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

    # Повторные попытки на случай временных сбоев API (503, rate limit)
    MAX_ATTEMPTS = 3
    RETRY_DELAY_SECONDS = 2

    async def get_forecast(self, latitude: float, longitude: float, days: int = 1):
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
                     "apparent_temperature_max,apparent_temperature_min,"
                     "precipitation_sum,precipitation_probability_max,"
                     "wind_speed_10m_max,wind_gusts_10m_max,uv_index_max,sunrise,sunset",
            "forecast_days": days,
            "timezone": "auto",
        }

        last_error = None
        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            try:
                async with globals.aiohttp_session.get(self.FORECAST_URL, params=params) as resp:
                    resp.raise_for_status()
                    return await resp.json()
            except ClientResponseError as exc:
                # Клиентская ошибка (400, 404...) не станет успешной от повтора — бросаем сразу
                if exc.status < 500 and exc.status != 429:
                    raise
                last_error = exc
                if attempt < self.MAX_ATTEMPTS:
                    delay = self.RETRY_DELAY_SECONDS * attempt
                    print(f"[weather] API вернул {exc.status}, повтор через {delay}с "
                          f"(попытка {attempt + 1} из {self.MAX_ATTEMPTS})")
                    await asyncio.sleep(delay)

        raise last_error


weather_client = WeatherClient()
