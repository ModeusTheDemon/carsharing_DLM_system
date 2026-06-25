# main.py
import os
from celery import Celery
from celery.schedules import crontab

from jobs.archiver import run_archiver
from jobs.anonymizer import run_anonymizer
from jobs.cleaner import run_cleaner

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery("dlm_workers", broker=REDIS_URL, backend=REDIS_URL)

# Настройки Celery
app.conf.update(
    timezone="Europe/Moscow",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_default_queue = "DLM_tasks"
)

# Обертываем наши функции в задачи Celery
@app.task(name="tasks.archive_old_rides")
def task_archive_old_rides():
    run_archiver()

@app.task(name="tasks.anonymize_users")
def task_anonymize_users():
    run_anonymizer()

@app.task(name="tasks.clean_old_archives")
def task_clean_old_archives():
    run_cleaner()

# Настраиваем ритмичное расписание (Celery Beat Schedule)
app.conf.beat_schedule = {
    # 1. Архивация запускается каждый день в полночь
    "archive-every-night": {
        "task": "tasks.archive_old_rides",
        "schedule": crontab(hour=0, minute=0),
    },
    # 2. Анонимизация запускается каждый час (на 0-й минуте)
    "anonymize-every-hour": {
        "task": "tasks.anonymize_users",
        "schedule": crontab(minute=0),
    },
    # 3. Полная очистка древнего архива запускается раз в неделю (в воскресенье в 2 часа ночи)
    "clean-archives-weekly": {
        "task": "tasks.clean_old_archives",
        "schedule": crontab(day_of_week=0, hour=2, minute=0),
    },
}