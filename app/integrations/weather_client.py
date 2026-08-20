from app.core import globals


class WeatherClient:
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

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
        async with globals.aiohttp_session.get(self.FORECAST_URL, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()


weather_client = WeatherClient()