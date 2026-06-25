#!/bin/bash
set -e

# Дописываем разрешение на репликацию в конфиг
echo "host replication postgres all scram-sha-256" >> "$PGDATA/pg_hba.conf"

# Принудительно заставляем Postgres перечитать этот файл
pg_ctl reload
