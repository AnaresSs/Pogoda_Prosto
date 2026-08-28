from pytest import mark

from app.bot.notifications.weather_message import (
    describe_weather,
    days_word,
    format_precip,
    format_temp,
    format_wind,
    format_weather_forecast,
    format_weather_message,
    get_daily_value,
)


# Правильное склонение слова "день" в шапке прогноза.
# Кейсы покрывают правила и их исключения: 11-14 → "дней", 21/22 → "день"/"дня"
@mark.parametrize("count, expected", [
    (1, "день"),
    (2, "дня"),
    (5, "дней"),
    (11, "дней"),
    (12, "дней"),
    (21, "день"),
    (22, "дня"),
])
def test_days_word(count, expected):
    assert days_word(count) == expected


# Мелкие форматтеры отдельных значений: нормальный случай, None, краевые значения
@mark.parametrize("value, expected", [
    (20, "+20°C"),
    (-3.7, "-4°C"),
    (None, "—"),
])
def test_format_temp(value, expected):
    assert format_temp(value) == expected


@mark.parametrize("value, expected", [
    (30.4, "30%"),
    (None, "—"),
])
def test_format_precip(value, expected):
    assert format_precip(value) == expected


# Ветер конвертируется км/ч → м/с: 36 км/ч = 10 м/с
@mark.parametrize("value, expected", [
    (36.0, "до 10.0 м/с"),
    (None, "—"),
])
def test_format_wind(value, expected):
    assert format_wind(value) == expected


# Код погоды Open-Meteo → человеческое описание; неизвестный/отсутствующий — нейтрально
@mark.parametrize("code, expected", [
    (0, "ясно ☀️"),
    (61, "небольшой дождь 🌧️"),
    (999, "погода без осадков"),
    (None, "погода без осадков"),
])
def test_describe_weather(code, expected):
    assert describe_weather(code) == expected


# Безопасное чтение значения из daily-массива ответа API
@mark.parametrize("daily, key, index, default, expected", [
    ({"temp": [10, 20]}, "temp", 1, None, 20),          # обычное значение
    ({}, "temp", 0, None, None),                        # ключа нет
    ({"temp": [10]}, "temp", 5, None, None),            # индекс за пределами массива
    ({"temp": []}, "temp", 0, "x", "x"),                # пустой список → default
])
def test_get_daily_value(daily, key, index, default, expected):
    assert get_daily_value(daily, key, index, default) == expected


# Сборка полного сообщения «погода на сегодня»
class TestFormatWeatherMessage:
    # Стандартная заглушка ответа Open-Meteo для всех тестов класса
    def make_weather(self):
        return {
            "current": {"temperature_2m": 20.0, "weather_code": 0},
            "daily": {
                "weather_code": [3],
                "temperature_2m_max": [25.0],
                "temperature_2m_min": [15.0],
                "precipitation_probability_max": [40],
                "wind_speed_10m_max": [18.0],
                "sunrise": ["2026-08-21T05:30"],
                "sunset": ["2026-08-21T20:45"],
            },
        }

    # Город пользователя присутствует в шапке сообщения
    def test_contains_city_name(self):
        text = format_weather_message(self.make_weather(), "Москва")
        assert "Москва" in text

    # Без города в шапке нет висячего разделителя "·"
    def test_header_without_city_has_no_separator_tail(self):
        text = format_weather_message(self.make_weather())
        assert "·" not in text

    # Текущая температура попала в текст
    def test_contains_current_temp(self):
        text = format_weather_message(self.make_weather(), "Сочи")
        assert "+20°C" in text

    # Ветер только в м/с, следы старого формата км/ч недопустимы
    def test_wind_in_ms_not_kmh(self):
        text = format_weather_message(self.make_weather(), "Сочи")
        assert "м/с" in text
        assert "км/ч" not in text

    # УФ-индекс удалён из сообщения по требованию
    def test_uv_index_removed(self):
        text = format_weather_message(self.make_weather(), "Сочи")
        assert "УФ" not in text

    # От timestamps рассвета/заката остаётся только время ЧЧ:ММ
    def test_sunrise_time_extracted(self):
        text = format_weather_message(self.make_weather(), "Сочи")
        assert "05:30" in text
        assert "2026-08-21T05:30" not in text

    # День и ночь — отдельные строки, а не «max / min» в одной
    def test_day_and_night_separate_lines(self):
        text = format_weather_message(self.make_weather(), "Сочи")
        assert "<b>Днём:</b> +25°C" in text
        assert "<b>Ночью:</b> +15°C" in text

    # Осадки помечены как значение за весь день, а не текущее
    def test_precip_labeled_for_whole_day(self):
        text = format_weather_message(self.make_weather(), "Сочи")
        assert "Осадки за день:" in text

    def test_wind_labeled_for_whole_day(self):
        text = format_weather_message(self.make_weather(), "Сочи")
        assert "Ветер за день:" in text


# Сборка многострочного прогноза на N дней
class TestFormatWeatherForecast:
    # Заглушка прогноза с указанным числом дней
    def make_forecast(self, days=3):
        return {
            "daily": {
                "time": [f"2026-08-{20 + i}" for i in range(1, days + 1)],
                "weather_code": [0] * days,
                "temperature_2m_max": [20.0] * days,
                "temperature_2m_min": [10.0] * days,
                "precipitation_probability_max": [10] * days,
                "wind_speed_10m_max": [10.8] * days,
            },
        }

    # Число дней и слово в заголовке согласованы ("на 3 дня")
    def test_header_contains_days_count_and_word(self):
        text = format_weather_forecast(self.make_forecast(3), "Казань")
        assert "Прогноз на 3 дня" in text

    def test_header_contains_city(self):
        text = format_weather_forecast(self.make_forecast(), "Казань")
        assert "Казань" in text

    # На каждый день приходится ровно один блок 📅
    def test_block_per_day(self):
        text = format_weather_forecast(self.make_forecast(7), "Казань")
        assert text.count("📅") == 7

    # Дата форматируется как ДД.ММ с днём недели в скобках
    def test_date_formatted_dd_mm_with_weekday(self):
        text = format_weather_forecast(self.make_forecast(1), "Казань")
        assert "21.08 (пт)" in text
