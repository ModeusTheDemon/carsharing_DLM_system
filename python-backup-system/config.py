import os

class Settings:
    # Собираем URL для подключения к PostgreSQL (psycopg3 драйвер)
    # Поддержка как Docker окружения, так и локальной разработки
    DATABASE_URL = os.getenv("DB_USER", "")

    if not DATABASE_URL:
        DB_USER = os.getenv("DB_USER", "postgres")
        DB_PASSWORD = os.getenv("DB_PASSWORD", "1092387456XxXYyYZzZ.,..,..,.")
        DB_HOST = os.getenv("DB_HOST", "postgres")  # Используем имя сервиса в Docker
        DB_PORT = os.getenv("DB_PORT", "5432")
        DB_NAME = os.getenv("DB_NAME", "carsharing_db")

        DATABASE_URL: str = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

settings = Settings()