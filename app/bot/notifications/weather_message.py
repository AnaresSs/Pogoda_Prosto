from datetime import datetime

WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]

WEATHER_DESCRIPTIONS = {
    0: "ясно ☀️",
    1: "малооблачно ⛅",
    2: "облачно 🌥️",
    3: "пасмурно ☁️",
    45: "туман 🌫️",
    48: "туман 🌫️",
    51: "морось 🌦️",
    53: "морось 🌦️",
    55: "морось 🌦️",
    61: "небольшой дождь 🌧️",
    63: "дождь 🌧️",
    65: "сильный дождь 🌧️",
    71: "небольшой снег 🌨️",
    73: "снег 🌨️",
    75: "сильный снег ❄️",
    80: "ливень 🌦️",
    81: "ливень 🌧️",
    82: "сильный ливень ⛈️",
    95: "гроза ⛈️",
    96: "гроза с градом ⛈️",
    99: "гроза с градом ⛈️",
}


def get_daily_value(daily, key, index, default=None):
    values = daily.get(key)
    if not values or index >= len(values):
        return default
    return values[index]


def format_temp(value):
    return f"{value:+.0f}°C" if value is not None else "—"


def format_precip(value):
    return f"{value:.0f}%" if value is not None else "—"


def format_wind(value):
    return f"до {value / 3.6:.1f} м/с" if value is not None else "—"


def describe_weather(code):
    if code is None:
        return "погода без осадков"
    return WEATHER_DESCRIPTIONS.get(code, "погода без осадков")


def days_word(count):
    if count % 10 == 1 and count % 100 != 11:
        return "день"
    if count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
        return "дня"
    return "дней"


def format_city_header(city_name=""):
    title = "🌀 <b>Погода Просто</b>"
    if city_name:
        return f"{title} · {city_name}"
    return title


def format_weather_message(weather, city_name="") -> str:
    current = weather.get("current") or {}
    daily = weather.get("daily") or {}

    current_desc = describe_weather(current.get("weather_code"))
    current_temp_str = format_temp(current.get("temperature_2m"))

    daily_desc = describe_weather(get_daily_value(daily, "weather_code", 0))
    temp_max_str = format_temp(get_daily_value(daily, "temperature_2m_max", 0))
    temp_min_str = format_temp(get_daily_value(daily, "temperature_2m_min", 0))

    precip_str = format_precip(get_daily_value(daily, "precipitation_probability_max", 0))
    wind_str = format_wind(get_daily_value(daily, "wind_speed_10m_max", 0))

    sunrise = get_daily_value(daily, "sunrise", 0)
    sunset = get_daily_value(daily, "sunset", 0)
    sunrise_str = sunrise[11:16] if sunrise else "—"
    sunset_str = sunset[11:16] if sunset else "—"

    return f'''{format_city_header(city_name)}

<b>Сейчас:</b> {current_temp_str}, {current_desc}
<b>Днём:</b> {temp_max_str} / ночью {temp_min_str}, {daily_desc}

💧 <b>Осадки:</b> {precip_str}
💨 <b>Ветер:</b> {wind_str}

🌅 <b>Рассвет:</b> {sunrise_str}
🌇 <b>Закат:</b> {sunset_str}

Хорошего дня! 🌀'''


def format_weather_forecast(weather, city_name=""):
    daily = weather.get("daily") or {}
    times = daily.get("time") or []

    header = f'{format_city_header(city_name)}\n<b>Прогноз на {len(times)} {days_word(len(times))}</b>'

    blocks = []
    for index in range(len(times)):
        day = datetime.strptime(times[index], "%Y-%m-%d")
        date_str = f"{day.day:02d}.{day.month:02d} ({WEEKDAYS[day.weekday()]})"

        desc = describe_weather(get_daily_value(daily, "weather_code", index))
        temp_max_str = format_temp(get_daily_value(daily, "temperature_2m_max", index))
        temp_min_str = format_temp(get_daily_value(daily, "temperature_2m_min", index))
        precip_str = format_precip(get_daily_value(daily, "precipitation_probability_max", index))
        wind_str = format_wind(get_daily_value(daily, "wind_speed_10m_max", index))

        blocks.append(f"📅 {date_str}\n{desc}, {temp_max_str} / {temp_min_str}\n"
                      f"💧 Осадки: {precip_str}\n💨 Ветер: {wind_str}")

    return f"{header}\n\n" + "\n\n".join(blocks)