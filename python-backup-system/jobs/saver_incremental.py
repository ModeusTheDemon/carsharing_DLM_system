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
from utils.backup_verifier import verify_backup
from utils.find_latest_backup import find_latest_backups
from utils.rotator import run_backup_rotation

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - [%(filename)s] - %(message)s"
)
logger = logging.getLogger(__name__)

# Путь к манифесту, который был сохранен после полного сохранения
MANIFEST_STORAGE_DIR = os.path.join(os.getcwd(), "backup_meta")
LAST_MANIFEST_PATH = os.path.join(MANIFEST_STORAGE_DIR, "backup_manifest")


def run_incremental_saver():
    """Джоба ИНКРЕМЕНТАЛЬНОГО физического сохранения базы данных (Incremental Backup)."""
    logger.info("=== STARTING INCREMENTAL PHYSICAL BACKUP JOB ===")

    rules_engine = RetentionRulesEngine()

    # Проверяем наличие базового манифеста
    if not os.path.exists(LAST_MANIFEST_PATH):
        logger.error(
            f"Critical Error: Base backup_manifest not found at {LAST_MANIFEST_PATH}! "
            "Incremental backup is impossible without a prior Full Backup."
        )
        raise FileNotFoundError("Base backup_manifest missing. Run Full Backup job first.")

    DB_USER = Settings.DB_USER
    DB_PASSWORD = Settings.DB_PASSWORD
    DB_HOST = Settings.DB_HOST
    DB_PORT = Settings.DB_PORT

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # Временная папка для генерации инкрементальных файлов
    temp_backup_dir = os.path.join(os.getcwd(), f"temp_phys_incr_backup_{timestamp}")

    try:
        # Валидация доступности БД
        with get_db() as db:
            logger.info("Verifying database connection via SQLAlchemy...")
            db.execute(text("SELECT 1"))
            logger.info("Database connection verified successfully.")

        env = os.environ.copy()
        env["PGPASSWORD"] = DB_PASSWORD

        logger.info(f"Launching pg_basebackup with incremental flag using manifest: {LAST_MANIFEST_PATH}")

        # Команда инкрементального копирования для PostgreSQL 17
        backup_cmd = [
            "pg_basebackup",
            "-h", DB_HOST,
            "-p", DB_PORT,
            "-U", DB_USER,
            "-D", temp_backup_dir,  # Директория для временных файлов
            "-Ft",  # Формат 'tar'
            "-z",  # Сжатие gzip на лету (.tar.gz)
            "-X", "stream",  # Включает WAL-логи инкрементального периода
            "--incremental", LAST_MANIFEST_PATH  # КЛЮЧЕВОЙ ФЛАГ PG 17: передаем базовый манифест
        ]

        # Запуск системной утилиты внутри контейнера воркера
        result = subprocess.run(backup_cmd, env=env, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"pg_basebackup incremental failed with error: {result.stderr}")

        logger.info(f"Master incremental backup successfully created in temp directory: {temp_backup_dir}")

        # === ВЕРИФИКАЦИЯ ИНКРЕМЕНТА ПЕРЕД ЗАПИСЬЮ НА ДИСКИ ===
        logger.info("Launching post-backup incremental integrity validation...")
        try:
            # Находим родительский полный бэкап
            latest_full, _ = find_latest_backups()

            # Запускаем верификацию инкремента с указанием пути к его полному родителю
            if not verify_backup(temp_backup_dir, parent_backup_path=latest_full):
                raise RuntimeError("Downloaded incremental backup files failed pg_verifybackup validation check!")
            logger.info("Incremental backup integrity verification passed successfully.")

            run_backup_rotation()
        except FileNotFoundError:
            raise RuntimeError("Verification impossible: parent full backup not found on disks!")
        # ====================================================

        # Поиск дисков и копирование измененных архивов
        disks = get_all_disks()
        logger.info(f"Target disks found for incremental backup: {disks}")
        backup_files = os.listdir(temp_backup_dir)

        for disk in disks:
            # Создаем на каждом диске обособленную папку для ИНКРЕМЕНТАЛЬНЫХ бэкапов
            target_dir = os.path.join(disk, "db_physical_incremental_backups", f"backup_{timestamp}")
            try:
                os.makedirs(target_dir, exist_ok=True)
                for file_name in backup_files:
                    shutil.copy2(os.path.join(temp_backup_dir, file_name), os.path.join(target_dir, file_name))
                logger.info(f"Incremental physical backup components successfully saved to: {target_dir}")
            except Exception as disk_err:
                logger.error(f"Failed to write incremental backup to disk {disk}. Error: {disk_err}")

        config_summary = rules_engine.get_config_summary()
        logger.info(f"Incremental backup job completed successfully. Config summary:\n{config_summary}")

    except Exception as e:
        error_config = rules_engine.get_error_handling_config()
        logger.error(f"Incremental backup job failed: {e}. Retry configuration: {error_config}")
        logger.error(f"Error details:\n{traceback.format_exc()}")
        raise

    finally:
        # Гарантированно очищаем временные файлы
        if os.path.exists(temp_backup_dir):
            try:
                shutil.rmtree(temp_backup_dir)
                logger.info("Temporary incremental backup directory cleared.")
            except Exception as clean_err:
                logger.warning(f"Could not remove temporary directory: {clean_err}")


if __name__ == "__main__":
    run_incremental_saver()
