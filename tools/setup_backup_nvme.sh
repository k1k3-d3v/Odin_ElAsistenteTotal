#!/usr/bin/env bash

set -euo pipefail

UUID="6B37-F9B4"
MOUNT_POINT="/mnt/backup_nvme"
FSTAB_LINE="UUID=$UUID $MOUNT_POINT exfat defaults,nofail,x-systemd.automount,uid=1000,gid=1000,umask=0077 0 0"

if [[ "$EUID" -ne 0 ]]; then
    exec sudo "$0" "$@"
fi

mkdir -p "$MOUNT_POINT"

if ! grep -q "UUID=$UUID" /etc/fstab; then
    cp /etc/fstab "/etc/fstab.odin-backup-$(date +%Y%m%d-%H%M%S)"
    printf '%s\n' "$FSTAB_LINE" >> /etc/fstab
fi

mount "$MOUNT_POINT" 2>/dev/null || true
findmnt "$MOUNT_POINT"
