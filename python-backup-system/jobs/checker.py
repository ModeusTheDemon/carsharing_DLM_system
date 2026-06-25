import logging
import time
import traceback
from sqlalchemy import text

from database.session import get_db
from utils.backuper import run_backuper
from utils.find_latest_backup import find_latest_backups
from utils.backup_verifier import verify_backup
from .saver_full import run_full_saver
from .saver_incremental import run_incremental_saver

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - [%(filename)s] - %(message)s"
)
logger = logging.getLogger(__name__)


def is_database_alive() -> bool:
    """Проверяет, отвечает ли база данных на SQL-запросы."""
    try:
        with get_db() as db:
            db.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.warning(f"Database ping failed! Error: {e}")
        return False


def run_checker():
    """Джоба-наблюдатель (watchdog)
        Проверяет работоспосбность бд, наличие бэкапов и их целостность, а так же количество.
    """
    logger.info("=== RUNNING DATABASE HEALTH CHECK ===")

    # Проверяем здоровье базы данных
    if is_database_alive():
        logger.info("Database status: HEALTHY. No action required.")

        try:
            # Получаем кортеж (latest_full, latest_incr)
            latest_full, latest_incr = find_latest_backups()

            logger.info("Backups status: exist! Starting integrity verification...")

            # Всегда сначала проверяем полный бэкап (1 аргумент)
            full_is_ok = verify_backup(latest_full)

            # Если есть инкремент и полный бэкап цел, проверяем инкремент (2 аргумента)
            if latest_incr and full_is_ok:
                verify_backup(latest_incr, parent_backup_path=latest_full)

        except FileNotFoundError:
            # Сюда мы попадаем, если find_latest_backups выбросила исключение (бэкапов нет)
            logger.warning("Backups status: doesn't exist! Proceed with full and incremental save.")
            run_full_saver()
            run_incremental_saver()

        return

    # Если база не ответила, даем ей второй и третий шансы через 5 секунд (защита от ложных срабатываний)
    for i in range(2):
        logger.warning("Database seems down. Re-trying in 5 seconds for confirmation...")
        time.sleep(5)

        if is_database_alive():
            logger.info("Database recovered after retry. Status: HEALTHY.")
            return

    # 3. База гарантированно мертва. Начинаем процесс самовосстановления (Self-Healing)
    logger.critical("DATABASE IS DOWN! Starting emergency disaster recovery procedure...")

    try:
        import docker
        # Подключаемся к Docker-демону хоста
        client = docker.from_env()

        # Имя контейнера базы данных из вашего docker-compose.yml
        POSTGRES_CONTAINER_NAME = "carsharing-postgres"

        # Принудительно останавливаем контейнер СУБД, чтобы освободить файлы тома
        try:
            logger.info(f"Stopping container '{POSTGRES_CONTAINER_NAME}' to prevent data corruption...")
            container = client.containers.get(POSTGRES_CONTAINER_NAME)
            container.stop(timeout=10)
            logger.info("Container stopped successfully.")
        except docker.errors.NotFound:
            logger.warning(f"Container '{POSTGRES_CONTAINER_NAME}' not found. It might be already deleted or renamed.")
        except Exception as docker_err:
            logger.error(f"Could not stop container: {docker_err}. Proceeding with file restoration anyway...")

        # Вызываем нашу аварийнную джобу восстановления файлов
        logger.info("Invoking emergency file restoration job...")
        try:
            run_backuper()
        except FileNotFoundError as e:
            logger.critical(f"Disaster recovery FAILED: {e}")
            logger.critical("No backups available for restoration. Please create a full backup first by running:")
            logger.critical("  python -m jobs.saver_full")
            logger.critical("Then restart the database container manually.")
            raise RuntimeError("Disaster recovery impossible without backups. Create full backup first.")

        # Запускаем контейнер базы данных обратно
        logger.info(f"Starting container '{POSTGRES_CONTAINER_NAME}' back up...")
        try:
            container = client.containers.get(POSTGRES_CONTAINER_NAME)
            container.start()
            logger.info("=======================================================")
            logger.critical("SELF-HEALING COMPLETED! Database container is starting up in RECOVERY mode.")
            logger.info("=======================================================")
        except Exception as start_err:
            logger.critical(
                f"Failed to automatically start container back! You must start it manually. Error: {start_err}")

    except Exception as master_ex:
        logger.critical(f"Self-healing orchestrator failed: {master_ex}")
        logger.error(f"Details:\n{traceback.format_exc()}")
        raise


if __name__ == "__main__":
    run_checker()
