# backup.Dockerfile
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Устанавливаем только легкий клиент и docker-cli
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    postgresql-client \
    docker.io \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Создаем симлинк-обманку для pg_verifybackup, чтобы она не ругалась на отсутствие pg_waldump
RUN ln -s /usr/bin/pg_verifybackup /usr/bin/pg_waldump

# Копируем и устанавливаем зависимости Python из общего корня проекта
COPY ./requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем исходный код бэкап-системы
COPY ./python-backup-system .
