from dotenv import load_dotenv
import os
from datetime import datetime

from sqlalchemy import URL

load_dotenv()

TOKEN = os.getenv('TOKEN')

# Реквизиты БД по частям; SQLALCHEMY_URL целиком имеет приоритет
# (используется в docker-compose для переопределения хоста на postgres)
SQLALCHEMY_URL = os.getenv('SQLALCHEMY_URL') or str(URL.create(
    drivername='postgresql+asyncpg',
    username=os.getenv('POSTGRES_USER', 'weather_db'),
    password=os.getenv('POSTGRES_PASSWORD', ''),
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    port=int(os.getenv('POSTGRES_PORT', '5432')),
    database=os.getenv('POSTGRES_DB', 'weather_db'),
))

SUPER_ADMIN_ID = int(os.getenv('SUPER_ADMIN_ID'))
ADMIN_IDS = [SUPER_ADMIN_ID]
ADMIN_GROUP_ID = os.getenv('ADMIN_GROUP_ID')

# Username разработчика для кнопки поддержки (без @)
SUPPORT_USERNAME = os.getenv('SUPPORT_USERNAME', '')


SERVER_IP = os.getenv('SERVER_IP')
NATS_URL = os.getenv('NATS_URL')

NATS_STREAM_NAME = os.getenv('NATS_STREAM_NAME', 'WEATHER')
NATS_STREAM_SUBJECTS = [s.strip() for s in os.getenv('NATS_STREAM_SUBJECTS', 'weather.>').split(',')]
NATS_SENDER_CONSUMER = os.getenv('NATS_SENDER_CONSUMER', 'sender')

NATS_ADMIN_STREAM_NAME = os.getenv('NATS_ADMIN_STREAM_NAME', 'ADMIN_MAILING')
NATS_ADMIN_STREAM_SUBJECTS = [s.strip() for s in os.getenv('NATS_ADMIN_STREAM_SUBJECTS', 'admin.mailing.>').split(',')]
NATS_ADMIN_SENDER_CONSUMER = os.getenv('NATS_ADMIN_SENDER_CONSUMER', 'admin_mailing')

# Максимальное число доставок задачи и время ожидания ack (секунды)
NATS_MAX_DELIVER = int(os.getenv('NATS_MAX_DELIVER', '3'))
NATS_ACK_WAIT_SECONDS = int(os.getenv('NATS_ACK_WAIT_SECONDS', '300'))

# Час локального времени города для ежедневной рассылки (по умолчанию 07:00)
SEND_HOUR = int(os.getenv('SEND_HOUR', '7'))

# Поиск ближайшего города по геолокации
GEO_SEARCH_RADIUS_KM = float(os.getenv('GEO_SEARCH_RADIUS_KM', '75'))
GEO_SEARCH_DELTA_DEGREES = float(os.getenv('GEO_SEARCH_DELTA_DEGREES', '1.0'))

# Ретраи Open-Meteo при временных сбоях
WEATHER_MAX_ATTEMPTS = int(os.getenv('WEATHER_MAX_ATTEMPTS', '3'))
WEATHER_RETRY_DELAY_SECONDS = int(os.getenv('WEATHER_RETRY_DELAY_SECONDS', '2'))
