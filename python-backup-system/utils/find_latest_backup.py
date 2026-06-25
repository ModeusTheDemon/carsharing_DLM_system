import os
import logging

from typing import Tuple
from utils.disck_getter import get_all_disks

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - [%(filename)s] - %(message)s"
)
logger = logging.getLogger(__name__)

def find_latest_backups() -> Tuple[str, str]:
    """Находит на дисках самый свежий полный бэкап и последний инкремент к нему."""
    disks = get_all_disks()
    full_backups = []
    incr_backups = []

    for disk in disks:
        full_dir = os.path.join(disk, "db_physical_full_backups")
        incr_dir = os.path.join(disk, "db_physical_incremental_backups")

        if os.path.exists(full_dir):
            for d in os.listdir(full_dir):
                full_backups.append(os.path.join(full_dir, d))

        if os.path.exists(incr_dir):
            for d in os.listdir(incr_dir):
                incr_backups.append(os.path.join(incr_dir, d))

    if not full_backups:
        raise FileNotFoundError("CRITICAL ERROR: not found any full physical copies!")

    # Сортируем по времени изменения папки (выбираем самый свежий)
    latest_full = max(full_backups, key=os.path.getmtime)
    logger.info(f"Found base full copy: {latest_full}")

    # Ищем инкремент, который был сделан строго после этого полного бэкапа
    latest_incr = None
    if incr_backups:
        valid_incrs = [i for i in incr_backups if os.path.getmtime(i) > os.path.getmtime(latest_full)]
        if valid_incrs:
            latest_incr = max(valid_incrs, key=os.path.getmtime)
            logger.info(f"Found latest weekly increment: {latest_incr}")

    return latest_full, latest_incr