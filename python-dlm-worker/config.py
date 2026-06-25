import os

class Settings:
    # Собираем URL для подключения к PostgreSQL (psycopg3 драйвер)
    # Поддержка как Docker окружения (DATABASE_URL), так и локальной разработки
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:1092387456XxXYyYZzZ.,..,..,.@postgres:5432/carsharing_db")

settings = Settings()