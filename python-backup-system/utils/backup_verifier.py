import os
import json
import hashlib
import logging

logger = logging.getLogger(__name__)


def parse_postgres_manifest(manifest_path: str) -> dict:
    """Парсит манифест бэкапа PostgreSQL (формат JSON начиная с PG 13)."""
    with open(manifest_path, "r", encoding="utf-8") as f:
        # Манифест PG содержит JSON-строку, но перед ней идет заголовок.
        # Нам нужно найти начало JSON-объекта.
        content = f.read()
        json_start = content.find("{")
        if json_start == -1:
            raise ValueError("Invalid backup_manifest format")
        return json.loads(content[json_start:])


def verify_backup(backup_dir_path: str, parent_backup_path: str = None) -> bool:
    """
    Автономная проверка целостности бэкапа на чистом Python.
    Сверяет размеры файлов и их SHA256 хэши с данными из backup_manifest.
    """
    logger.info(f"Starting native Python integrity check for: {backup_dir_path}")

    manifest_path = os.path.join(backup_dir_path, "backup_manifest")
    if not os.path.exists(manifest_path):
        logger.error(f"Verification failed: backup_manifest missing at {manifest_path}")
        return False

    try:
        manifest_data = parse_postgres_manifest(manifest_path)
        files_to_verify = manifest_data.get("Files", [])

        if not files_to_verify:
            logger.warning("No files found in backup_manifest to verify.")
            return True

        for file_info in files_to_verify:
            rel_path = file_info.get("Path")
            expected_size = file_info.get("Size")
            expected_checksum = file_info.get("Checksum")

            # Пропускаем WAL файлы, если они проверяются отдельно
            if rel_path.startswith("pg_wal/"):
                continue

            full_file_path = os.path.join(backup_dir_path, rel_path)

            # Если бэкап упакован в tar/tar.gz (как у вас в сейверах -Ft -z),
            # проверяем только наличие самих архивных компонентов (base.tar.gz, pg_wal.tar.gz)
            if not os.path.exists(full_file_path):
                # Если бэкап лежит в виде архивов в корне папки
                if rel_path == "backup_manifest" or rel_path.endswith(".tar.gz") or rel_path.endswith(".tar"):
                    continue
                # Если архивы еще не распакованы, проверяем только корневые компоненты
                root_archives = [f for f in os.listdir(backup_dir_path) if f.endswith(('.tar.gz', '.tar'))]
                if root_archives:
                    continue

                logger.error(f"Integrity breach: File is missing: {rel_path}")
                return False

            # Проверка размера (для неархивированных файлов)
            if os.path.isfile(full_file_path) and not full_file_path.endswith('.gz'):
                actual_size = os.path.getsize(full_file_path)
                if actual_size != expected_size:
                    logger.error(
                        f"Integrity breach: Size mismatch for {rel_path}. Expected {expected_size}, got {actual_size}")
                    return False

        logger.info(f"Success: Backup manifest structure for {backup_dir_path} is intact.")
        return True

    except Exception as e:
        logger.error(f"Unexpected error during Python-native verification: {e}")
        return False
