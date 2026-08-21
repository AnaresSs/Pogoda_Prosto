import os

# Заглушки переменных окружения для запуска тестов там, где нет .env
# (GitHub Actions). Реальные значения не нужны: тестируем логику, а не подключение.
os.environ.setdefault("TOKEN", "test-token")
os.environ.setdefault("SQLALCHEMY_URL", "postgresql+asyncpg://test:test@localhost:5433/weather_test")
os.environ.setdefault("SUPER_ADMIN_ID", "1")
os.environ.setdefault("ADMIN_GROUP_ID", "-100")
os.environ.setdefault("SERVER_IP", "127.0.0.1")
os.environ.setdefault("NATS_URL", "nats://localhost:4222")

# Корневой conftest: pytest добавляет корень проекта в sys.path,
# чтобы тесты могли импортировать app.*
