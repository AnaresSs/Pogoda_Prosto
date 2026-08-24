from typing import Protocol


class WeatherProvider(Protocol):
    """Контракт поставщика погоды.

    Любой объект с методом get_forecast такой сигнатуры считается
    WeatherProvider — наследование не требуется (структурная типизация).
    Реализации: OpenMeteoProvider (прод), фейки в тестах, будущие API.
    """

    async def get_forecast(self, latitude: float, longitude: float, days: int = 1) -> dict:
        ...
