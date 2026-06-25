from typing import List
import logging
import os
import psutil

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - [%(filename)s] - %(message)s"
)
logger = logging.getLogger(__name__)

def get_all_disks() -> List[str]:
    """Возвращает список путей ко всем доступным дискам в системе."""
    logger.info("Getting available disks list")
    disks: List[str] = []

    # Список системных префиксов и типов ФС, которые нужно игнорировать в Linux/Docker
    ignored_prefixes = ('/etc', '/proc', '/sys', '/dev', '/run', '/boot', '/var/lib/postgresql', '/var/lib/postgresql/data')
    ignored_fstypes = ('tmpfs', 'devtmpfs', 'devpts', 'sysfs', 'proc', 'cgroup', 'overlay')

    try:
        for part in psutil.disk_partitions(all=True):
            # 1. Пропускаем CD-ROM на Windows
            if os.name == "nt" and "cdrom" in part.opts:
                continue

            # 2. Пропускаем известные виртуальные файловые системы
            if part.fstype in ignored_fstypes:
                continue

            # 3. Исключаем системные пути Linux
            if part.mountpoint.startswith(ignored_prefixes):
                continue

            # 4. Проверяем существование и что это именно директория (исправлен part)
            if os.path.exists(part.mountpoint) and os.path.isdir(part.mountpoint):
                # Избегаем дубликатов точек монтирования
                if part.mountpoint not in disks:
                    disks.append(part.mountpoint)

    except Exception as e:
        logger.error(f"Error occurred while scanning disks: {e}")

    return disks