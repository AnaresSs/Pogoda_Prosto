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


class TestDaysWord:
    def test_one_day(self):
        assert days_word(1) == "день"

    def test_two_days(self):
        assert days_word(2) == "дня"

    def test_five_days(self):
        assert days_word(5) == "дней"

    def test_eleven_days(self):
        assert days_word(11) == "дней"

    def test_twenty_one_days(self):
        assert days_word(21) == "день"

    def test_twelve_days(self):
        assert days_word(12) == "дней"


class TestFormatters:
    def test_format_temp_positive(self):
        assert format_temp(20) == "+20°C"

    def test_format_temp_negative_rounds(self):
        assert format_temp(-3.7) == "-4°C"

    def test_format_temp_none(self):
        assert format_temp(None) == "—"

    def test_format_precip(self):
        assert format_precip(30.4) == "30%"

    def test_format_precip_none(self):
        assert format_precip(None) == "—"

    def test_format_wind_converts_to_ms(self):
        assert format_wind(36.0) == "до 10.0 м/с"

    def test_format_wind_none(self):
        assert format_wind(None) == "—"

    def test_describe_weather_known_code(self):
        assert describe_weather(0) == "ясно ☀️"

    def test_describe_weather_none(self):
        assert describe_weather(None) == "погода без осадков"

    def test_describe_weather_unknown_code(self):
        assert describe_weather(999) == "погода без осадков"


class TestGetDailyValue:
    def test_returns_value(self):
        assert get_daily_value({"temp": [10, 20]}, "temp", 1) == 20

    def test_missing_key(self):
        assert get_daily_value({}, "temp", 0) is None

    def test_index_out_of_range(self):
        assert get_daily_value({"temp": [10]}, "temp", 5) is None

    def test_empty_list(self):
        assert get_daily_value({"temp": []}, "temp", 0, default="x") == "x"


class TestFormatWeatherMessage:
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

    def test_contains_city_name(self):
        text = format_weather_message(self.make_weather(), "Москва")
        assert "Москва" in text

    def test_header_without_city_has_no_separator_tail(self):
        text = format_weather_message(self.make_weather())
        assert "·" not in text

    def test_contains_current_temp(self):
        text = format_weather_message(self.make_weather(), "Сочи")
        assert "+20°C" in text

    def test_wind_in_ms_not_kmh(self):
        text = format_weather_message(self.make_weather(), "Сочи")
        assert "м/с" in text
        assert "км/ч" not in text

    def test_uv_index_removed(self):
        text = format_weather_message(self.make_weather(), "Сочи")
        assert "УФ" not in text

    def test_sunrise_time_extracted(self):
        text = format_weather_message(self.make_weather(), "Сочи")
        assert "05:30" in text
        assert "2026-08-21T05:30" not in text


class TestFormatWeatherForecast:
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

    def test_header_contains_days_count_and_word(self):
        text = format_weather_forecast(self.make_forecast(3), "Казань")
        assert "Прогноз на 3 дня" in text

    def test_header_contains_city(self):
        text = format_weather_forecast(self.make_forecast(), "Казань")
        assert "Казань" in text

    def test_block_per_day(self):
        text = format_weather_forecast(self.make_forecast(7), "Казань")
        assert text.count("📅") == 7

    def test_date_formatted_dd_mm_with_weekday(self):
        text = format_weather_forecast(self.make_forecast(1), "Казань")
        assert "21.08 (пт)" in text
