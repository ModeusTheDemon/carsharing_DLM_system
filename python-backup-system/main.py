# main.py
import os
from celery import Celery
from celery.schedules import crontab

from jobs.checker import run_checker
from jobs.backuper import run_backuper
from jobs.saver_incremental import run_saver_inc
from jobs.saver_full import run_saver_full

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery("backup_worker", broker=REDIS_URL, backend=REDIS_URL)

# Настройки Celery
app.conf.update(
    timezone="Europe/Moscow",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json"
)

# Обертываем наши функции в задачи Celery
@app.task(name="tasks.check_database_health")
def task_check_database():
    run_checker()

@app.task(name="tasks.save_increment")
def task_save_increment():
    run_saver_inc()

@app.task(name="tasks.save_full")
def task_save_full():
    run_saver_full()

# Настраиваем ритмичное расписание (Celery Beat Schedule)
app.conf.beat_schedule = {
    # 1. Проверка проводится каждые 5 минут или при уведомлении монитора
    "check-every-five-minutes": {
        "task": "tasks.check_database_health",
        "schedule": crontab(minute="*\5"),
    },
    # 2. бэкап инкремента проводится каждую неделю
    "save-increment-every-week": {
        "task": "tasks.save_increment",
        "schedule": crontab(minute=0, hour=1, day_of_week=1),
    },
    # 3. бэкап полный каждый месяц
    "save-full-every-mounth": {
        "task": "tasks.save_full",
        "schedule": crontab(),
    },
}