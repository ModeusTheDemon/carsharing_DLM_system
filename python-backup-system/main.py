import os
from celery import Celery
from celery.schedules import crontab

from jobs.checker import run_checker
# from jobs.backuper import run_backuper
from jobs.saver_incremental import run_incremental_saver
from jobs.saver_full import run_full_saver

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app: Celery = Celery("backup_worker", broker=REDIS_URL, backend=REDIS_URL)

# Настройки Celery
app.conf.update(
    timezone="Europe/Moscow",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_default_queue = "backup_tasks"
)

# Обертываем наши функции в задачи Celery
@app.task(name="tasks.check_database_health")
def task_check_database():
    run_checker()

@app.task(name="tasks.save_increment")
def task_save_increment():
    run_incremental_saver()

@app.task(name="tasks.save_full")
def task_save_full():
    run_full_saver()

# Настраиваем ритмичное расписание (Celery Beat Schedule)
app.conf.beat_schedule = {
    # 1. Проверка проводится каждые 5 минут (или при уведомлении монитора) TODO: сделать монитор(health monitor) (когда-нибудь)
    "check-every-five-minutes": {
        "task": "tasks.check_database_health",
        "schedule": crontab(minute="*/5"),
    },
    # 2. бэкап инкремента проводится каждую неделю
    "save-increment-every-week": {
        "task": "tasks.save_increment",
        "schedule": crontab(minute=0, hour=1, day_of_week=1),
    },
    # 3. бэкап полный каждый месяц
    "save-full-every-mounth": {
        "task": "tasks.save_full",
        "schedule": crontab(minute=0, hour=0, day_of_month=1),
    },
}