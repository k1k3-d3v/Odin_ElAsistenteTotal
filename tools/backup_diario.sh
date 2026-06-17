#!/usr/bin/env bash

set -euo pipefail

RESTIC_BIN="${RESTIC_BIN:-/home/k1k3/.local/bin/restic}"
RESTIC_REPOSITORY="${RESTIC_REPOSITORY:-/mnt/backup_nvme/odin-restic}"
RESTIC_PASSWORD_FILE="${RESTIC_PASSWORD_FILE:-/home/k1k3/odin/scripts/restic-password}"
LOG_DIR="/home/k1k3/odin/logs/backups"
DB_DUMP_DIR="/home/k1k3/odin/backups/db"

export RESTIC_REPOSITORY RESTIC_PASSWORD_FILE

mkdir -p "$LOG_DIR" "$DB_DUMP_DIR"

if ! mountpoint -q /mnt/backup_nvme; then
    echo "ERROR: el NVMe no está montado en /mnt/backup_nvme" >&2
    exit 1
fi

if [[ ! -x "$RESTIC_BIN" || ! -r "$RESTIC_PASSWORD_FILE" ]]; then
    echo "ERROR: falta Restic o su fichero de contraseña" >&2
    exit 1
fi

# Volcado consistente de MariaDB. Immich ya genera sus propios dumps diarios.
docker exec nextcloud-db sh -lc \
    'mariadb-dump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction --all-databases' \
    > "$DB_DUMP_DIR/nextcloud-all.sql"

"$RESTIC_BIN" backup \
    /home/k1k3/odin \
    /mnt/almacen/immich \
    --exclude-caches \
    --exclude='/home/k1k3/odin/core/odin-master/data/nextcloud_db/**' \
    --exclude='/home/k1k3/odin/scripts/restic-password' \
    --exclude='/home/k1k3/odin/core/odin-master/data/frigate/model_cache/**' \
    --exclude='**/node_modules/**' \
    --exclude='**/.venv/**' \
    --exclude='**/__pycache__/**' \
    --exclude='**/*.log' \
    --tag odin \
    --host odin

"$RESTIC_BIN" forget \
    --tag odin \
    --keep-daily 7 \
    --keep-weekly 4 \
    --keep-monthly 6 \
    --prune

"$RESTIC_BIN" check --read-data-subset=1/100

echo "Backup Restic de Odín completado: $(date --iso-8601=seconds)"
