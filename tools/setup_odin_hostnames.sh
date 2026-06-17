#!/usr/bin/env bash
set -euo pipefail

HOSTS_LINE="192.168.1.133 odin.webui odin.openwebui odin.immich odin.nextcloud odin.homeassistant odin.ha odin.n8n odin.netdata odin.frigate odin.qdrant odin.stirling odin.crawl odin.evolution odin.piper odin.whisper odin.asr odin.tts odin.ollama odin.mealie"

if [[ "${EUID}" -ne 0 ]]; then
  exec sudo "$0" "$@"
fi

if grep -q 'odin.immich' /etc/hosts; then
  perl -0pi -e "s/^.*odin\\.immich.*\\n/${HOSTS_LINE}\\n/m" /etc/hosts
else
  printf '\n%s\n' "${HOSTS_LINE}" >> /etc/hosts
fi

dscacheutil -flushcache 2>/dev/null || true
killall -HUP mDNSResponder 2>/dev/null || true

printf 'Odin hostnames installed:\n%s\n' "${HOSTS_LINE}"
