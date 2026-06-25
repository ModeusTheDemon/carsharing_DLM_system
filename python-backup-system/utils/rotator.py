import os
import shutil
import logging
from utils.disck_getter import get_all_disks

logger = logging.getLogger(__name__)


def run_backup_rotation():
    """
    Удерживает до 4-х последних версий полного бэкапа
    и до 3-х последних инкрементов для каждого из них.
    """
    logger.info("=== STARTING ADVANCED BACKUP ROTATION ENGINE (4 Full / 3 Incr) ===")
    disks = get_all_disks()

    for disk in disks:
        full_dir = os.path.join(disk, "db_physical_full_backups")
        incr_dir = os.path.join(disk, "db_physical_incremental_backups")

        # --- РАБОТА С ПОЛНЫМИ БЭКАПАМИ ---
        if not os.path.exists(full_dir):
            continue

        # Собираем все папки полных бэкапов и сортируем по времени изменения (от новых к старым)
        full_backups = [os.path.join(full_dir, d) for d in os.listdir(full_dir)]
        full_backups = [b for b in full_backups if os.path.isdir(b)]
        full_backups.sort(key=os.path.getmtime, reverse=True)

        # Выделяем бэкапы на сохранение и на удаление
        keep_full = full_backups[:4]
        delete_full = full_backups[4:]

        # Удаляем старые полные бэкапы (5-й, 6-й и т.д.)
        for old_full in delete_full:
            try:
                shutil.rmtree(old_full)
                logger.info(f"Rotator: Deleted expired FULL backup: {old_full}")
            except Exception as e:
                logger.error(f"Failed to delete old full backup {old_full}: {e}")

        # --- РАБОТА С ИНКРЕМЕНТАМИ ---
        if not os.path.exists(incr_dir):
            continue

        # Собираем все инкременты
        incr_backups = [os.path.join(incr_dir, d) for d in os.listdir(incr_dir)]
        incr_backups = [i for i in incr_backups if os.path.isdir(i)]

        # Группируем инкременты по их родительским полным бэкапам.
        # Для этого сопоставляем таймстампы из названий папок (backup_YYYYMMDD_HHMMSS)
        for full_path in keep_full:
            # full_timestamp = os.path.basename(full_path).replace("backup_", "")

            # Находим инкременты, созданные ПОСЛЕ этого полного бэкапа,
            # но ДО следующего (или просто привязанные по времени)
            related_incrs = [
                i for i in incr_backups
                if os.path.getmtime(i) > os.path.getmtime(full_path)
            ]

            # Если есть другие полные бэкапы, которые моложе текущего,
            # отсекаем инкременты, принадлежащие уже им
            younger_fulls = [f for f in keep_full if os.path.getmtime(f) > os.path.getmtime(full_path)]
            if younger_fulls:
                next_full_time = min(os.path.getmtime(f) for f in younger_fulls)
                related_incrs = [i for i in related_incrs if os.path.getmtime(i) < next_full_time]

            # Сортируем инкременты текущего полного бэкапа от новых к старым
            related_incrs.sort(key=os.path.getmtime, reverse=True)

            # Оставляем только 3 самых свежих инкремента для этого полного бэкапа
            # keep_incrs = related_incrs[:3]
            delete_incrs = related_incrs[3:]

            for old_incr in delete_incrs:
                try:
                    shutil.rmtree(old_incr)
                    logger.info(f"Rotator: Deleted excess INCREMENTAL backup: {old_incr}")
                except Exception as e:
                    logger.error(f"Failed to delete excess increment {old_incr}: {e}")

        # чистим сиротские инкременты (чьи полные бэкапы были только что удалены)
        # Если инкремент старше самого старого из сохраненных полных бэкапов — он идет под нож
        if keep_full:
            oldest_valid_full_time = os.path.getmtime(keep_full[-1])
            for incr in incr_backups:
                if os.path.exists(incr) and os.path.getmtime(incr) < oldest_valid_full_time:
                    try:
                        shutil.rmtree(incr)
                        logger.info(f"Rotator: Deleted orphan INCREMENTAL backup: {incr}")
                    except Exception as e:
                        logger.error(f"Failed to delete orphan increment {incr}: {e}")

    logger.info("=== BACKUP ROTATION COMPLETED SUCCESSFULLY ===")
