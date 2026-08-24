from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

TOKEN = os.getenv('TOKEN')
SQLALCHEMY_URL = os.getenv('SQLALCHEMY_URL')

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

# Час локального времени города для ежедневной рассылки (по умолчанию 07:00)
SEND_HOUR = int(os.getenv('SEND_HOUR', '7'))


