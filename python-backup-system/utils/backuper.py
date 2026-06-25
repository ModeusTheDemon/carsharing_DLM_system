import logging
import os
import shutil
import tarfile
import traceback
from utils.find_latest_backup import find_latest_backups


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - [%(filename)s] - %(message)s"
)
logger = logging.getLogger(__name__)


def run_backuper():
    """Главная аварийная джоба восстановления СУБД PostgreSQL 17."""
    logger.info("=======================================================")
    logger.critical("ATTENTION: BACKUP SYSTEM IS ACTIVE")
    logger.info("=======================================================")

    # Путь к папке данных PostgreSQL внутри контейнера воркера.
    # Этот путь должен смотреть на упавший том (volume) СУБД.
    TARGET_PG_DATA_DIR = os.getenv("TARGET_PG_DATA_DIR", "/var/lib/postgresql/data")

    try:
        # Поиск уцелевших файлов бэкапа
        full_backup_path, incr_backup_path = find_latest_backups()
        
        # Полная очистка поврежденного/упавшего каталога данных
        logger.warning(f"Clearing damaged data catalogue: {TARGET_PG_DATA_DIR}")
        if os.path.exists(TARGET_PG_DATA_DIR):
            for item in os.listdir(TARGET_PG_DATA_DIR):
                item_path = os.path.join(TARGET_PG_DATA_DIR, item)
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                except Exception as clean_err:
                    logger.warning(f"Can not delete this directory/file {item}: {clean_err}. Is it blocked?.")
        else:
            os.makedirs(TARGET_PG_DATA_DIR, exist_ok=True)

        # Распаковка ПОЛНОГО физического бэкапа
        base_tar = os.path.join(full_backup_path, "base.tar.gz")
        logger.info(f"Unpacking base DBMS file structure ({base_tar})...")
        with tarfile.open(base_tar, "r:gz") as tar:
            tar.extractall(path=TARGET_PG_DATA_DIR)

        # Накат ИНКРЕМЕНТАЛЬНОГО бэкапа поверх (если он существовал)
        if incr_backup_path:
            incr_tar = os.path.join(incr_backup_path, "base.tar.gz")
            logger.info(f"Addition of binary incremental changes ({incr_tar})...")
            with tarfile.open(incr_tar, "r:gz") as tar:
                tar.extractall(path=TARGET_PG_DATA_DIR)

        # Сборка и интеграция журналов транзакций (WAL)
        # Создаем временный буфер для слияния логов из полной и инкрементальной копий
        temp_wal_buffer = os.path.join(TARGET_PG_DATA_DIR, "pg_wal_recovery_buffer")
        os.makedirs(temp_wal_buffer, exist_ok=True)

        # Вытаскиваем WAL из полной копии
        with tarfile.open(os.path.join(full_backup_path, "pg_wal.tar.gz"), "r:gz") as tar:
            tar.extractall(path=temp_wal_buffer)

        # Вытаскиваем WAL из инкремента (они перезапишут старые логи более свежими транзакциями)
        if incr_backup_path:
            with tarfile.open(os.path.join(incr_backup_path, "pg_wal.tar.gz"), "r:gz") as tar:
                tar.extractall(path=temp_wal_buffer)

        # Переносим все собранные WAL-файлы в системную директорию pg_wal
        native_wal_dir = os.path.join(TARGET_PG_DATA_DIR, "pg_wal")
        os.makedirs(native_wal_dir, exist_ok=True)
        for wal_file in os.listdir(temp_wal_buffer):
            shutil.move(os.path.join(temp_wal_buffer, wal_file), os.path.join(native_wal_dir, wal_file))
        shutil.rmtree(temp_wal_buffer)

        # Создание триггера восстановления для PostgreSQL 17
        # Пустой файл recovery.signal заставит вошедшую в сеть базу понять, что она восстанавливается
        signal_file_path = os.path.join(TARGET_PG_DATA_DIR, "recovery.signal")
        with open(signal_file_path, "w") as f:
            f.write("")
        
        # Инструктируем конфигурационный файл СУБД докатить транзакции до самого актуального состояния LSN
        postgresql_conf_path = os.path.join(TARGET_PG_DATA_DIR, "postgresql.conf")
        with open(postgresql_conf_path, "a", encoding="utf-8") as f:
            f.write("\n# Инструкции автоматического восстановления Disaster Recovery\n")
            f.write("recovery_target_timeline = 'latest'\n")

        logger.info("=======================================================")
        logger.info("EMERGENCY FILE RECOVERY ENDED WELL!")
        logger.critical("you can start database container now")
        logger.info("=======================================================")

    except Exception as e:
        logger.critical(f"EMERGENCY FILE RECOVERY ENDED WITH ERROR: {e}")
        logger.error(f"Errors stack:\n{traceback.format_exc()}")
        raise


if __name__ == "__main__":
 run_backuper()
