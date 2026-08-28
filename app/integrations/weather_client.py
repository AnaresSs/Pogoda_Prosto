import asyncio
import logging

from aiohttp import ClientResponseError, ClientSession

from app.core.config import WEATHER_MAX_ATTEMPTS, WEATHER_RETRY_DELAY_SECONDS

logger = logging.getLogger(__name__)


class OpenMeteoProvider:
    """Реализация WeatherProvider на API open-meteo.com.

    Соответствует контракту WeatherProvider структурно: наследование не нужно.
    """

    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

    # Повторные попытки на случай временных сбоев API (503, rate limit)
    MAX_ATTEMPTS = WEATHER_MAX_ATTEMPTS
    RETRY_DELAY_SECONDS = WEATHER_RETRY_DELAY_SECONDS

    def __init__(self, http: ClientSession):
        # HTTP-сессия создаётся один раз в run.py и передаётся сюда
        self.http = http

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
                async with self.http.get(self.FORECAST_URL, params=params) as resp:
                    resp.raise_for_status()
                    return await resp.json()
            except ClientResponseError as exc:
                # Клиентская ошибка (400, 404...) не станет успешной от повтора — бросаем сразу
                if exc.status < 500 and exc.status != 429:
                    raise
                last_error = exc
                if attempt < self.MAX_ATTEMPTS:
                    delay = self.RETRY_DELAY_SECONDS * attempt
                    logger.warning("API вернул %s, повтор через %ss (попытка %d из %d)",
                                   exc.status, delay, attempt + 1, self.MAX_ATTEMPTS)
                    await asyncio.sleep(delay)

        raise last_error
