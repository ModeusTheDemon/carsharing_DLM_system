# Dockerfile (внутри папки python-dlm-worker)
FROM python:3.12-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Отключаем генерацию .pyc файлов и включаем моментальный вывод логов в консоль
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Копируем requirements.txt из корня проекта
COPY ./requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем код именно DLM-воркера внутрь папки /app контейнера
COPY ./python-dlm-worker .
