from datetime import datetime, timezone
import logging
import os
import shutil
import subprocess
import traceback
from sqlalchemy import text

from database.session import get_db
from config import Settings
from policies.rules_engine import RetentionRulesEngine
from utils.disck_getter import get_all_disks
from utils.backup_verifier import verify_backup  # Импорт функции верификации
from utils.rotator import run_backup_rotation

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - [%(filename)s] - %(message)s"
)
logger = logging.getLogger(__name__)

# Папка с манифест для инкрементальной джобы
MANIFEST_STORAGE_DIR = os.path.join(os.getcwd(), "backup_meta")
LAST_MANIFEST_PATH = os.path.join(MANIFEST_STORAGE_DIR, "backup_manifest")


def run_full_saver():
    """Джоба ПОЛНОГО физического сохранения базы данных (Full Backup)."""
    logger.info("=== STARTING FULL PHYSICAL BACKUP JOB ===")

    rules_engine = RetentionRulesEngine()

    DB_USER = Settings.DB_USER
    DB_PASSWORD = Settings.DB_PASSWORD
    DB_HOST = Settings.DB_HOST
    DB_PORT = Settings.DB_PORT

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # Временная папка для генерации файлов репликации
    temp_backup_dir = os.path.join(os.getcwd(), f"temp_phys_full_backup_{timestamp}")

    try:
        # Валидация доступности БД через вашу сессию SQLAlchemy
        with get_db() as db:
            logger.info("Verifying database connection via SQLAlchemy...")
            db.execute(text("SELECT 1"))
            logger.info("Database connection verified successfully.")

        # Безопасно передаем пароль через переменные окружения процесса
        env = os.environ.copy()
        env["PGPASSWORD"] = DB_PASSWORD

        logger.info("Launching pg_basebackup for FULL physical replication...")

        # Команда копирования для PostgreSQL 17
        backup_cmd = [
            "pg_basebackup",
            "-h", DB_HOST,
            "-p", DB_PORT,
            "-U", DB_USER,
            "-D", temp_backup_dir,  # Директория для временного сохранения файлов
            "-Ft",  # Формат 'tar' (упаковывает таблицы в base.tar)
            "-z",  # Сжатие gzip на лету (.tar.gz)
            "-X", "stream",  # Включает все активные WAL-логи для консистентности
        ]

        # Запуск системной утилиты внутри контейнера воркера
        result = subprocess.run(backup_cmd, env=env, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"pg_basebackup failed with error: {result.stderr}")

        logger.info(f"Master full backup successfully created in temp directory: {temp_backup_dir}")

        # === ВЕРИФИКАЦИЯ ЦЕЛОСТНОСТИ ПЕРЕД ЗАПИСЬЮ НА ДИСКИ ===
        logger.info("Launching post-backup integrity validation...")
        if not verify_backup(temp_backup_dir):
            raise RuntimeError("Downloaded physical backup files failed pg_verifybackup validation check!")
        logger.info("Backup integrity verification passed successfully. Proceeding to target disks distribution.")
        # ====================================================

        # Поиск дисков и копирование архивов
        disks = get_all_disks()
        logger.info(f"Target disks found for full backup: {disks}")
        backup_files = os.listdir(temp_backup_dir)

        for disk in disks:
            # Создаем на каждом диске обособленную папку для ПОЛНЫХ бэкапов
            target_dir = os.path.join(disk, "db_physical_full_backups", f"backup_{timestamp}")
            try:
                os.makedirs(target_dir, exist_ok=True)
                for file_name in backup_files:
                    shutil.copy2(os.path.join(temp_backup_dir, file_name), os.path.join(target_dir, file_name))
                logger.info(f"Full physical backup components successfully saved to: {target_dir}")
            except Exception as disk_err:
                logger.error(f"Failed to write full backup to disk {disk}. Error: {disk_err}")

        # КРИТИЧЕСКИЙ ШАГ ДЛЯ ИНКРЕМЕНТОВ: сохраняем файл манифеста локально
        # Вторая джоба будет брать этот файл, чтобы понять, какие байты изменились с этого момента
        os.makedirs(MANIFEST_STORAGE_DIR, exist_ok=True)
        shutil.copy2(os.path.join(temp_backup_dir, "backup_manifest"), LAST_MANIFEST_PATH)
        logger.info(f"Base backup_manifest successfully cached for future increments at: {LAST_MANIFEST_PATH}")

        run_backup_rotation()

        config_summary = rules_engine.get_config_summary()
        logger.info(f"Full backup job completed successfully. Config summary:\n{config_summary}")

    except Exception as e:
        error_config = rules_engine.get_error_handling_config()
        logger.error(f"Full backup job failed: {e}. Retry configuration: {error_config}")
        logger.error(f"Error details:\n{traceback.format_exc()}")
        raise

    finally:
        # Гарантированно очищаем тяжелые временные файлы
        if os.path.exists(temp_backup_dir):
            try:
                shutil.rmtree(temp_backup_dir)
                logger.info("Temporary backup directory cleared.")
            except Exception as clean_err:
                logger.warning(f"Could not remove temporary directory: {clean_err}")


if __name__ == "__main__":
    run_full_saver()
