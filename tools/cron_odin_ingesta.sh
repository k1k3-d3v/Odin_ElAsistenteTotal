#!/bin/bash

# --- CONFIGURACION ---
set -a
[ -f /home/k1k3/odin/scripts/telegram.env ] && . /home/k1k3/odin/scripts/telegram.env
set +a

TOKEN="${TELEGRAM_BOT_TOKEN:-${TOKEN:-}}"
CHAT_ID="${TELEGRAM_CHAT_ID:-${CHAT_ID:-}}"
PYTHON_BIN="/home/k1k3/env/bin/python3"
SCRIPT_PY="/home/k1k3/odin/scripts/odin_ingesta_master.py"

# --- EJECUCION ---
INICIO=$(date '+%Y-%m-%d %H:%M:%S')
LOG_SALIDA="$($PYTHON_BIN "$SCRIPT_PY" 2>&1)"
STATUS=$?
FIN=$(date '+%Y-%m-%d %H:%M:%S')

printf '%s\n' "[$INICIO] Inicio ingesta Odín"
printf '%s\n' "$LOG_SALIDA"
printf '%s\n' "[$FIN] Fin ingesta Odín (status=$STATUS)"

# --- LOGICA DE NOTIFICACION ---
NUEVOS=$(printf '%s\n' "$LOG_SALIDA" | grep -oP 'Procesando \K[0-9]+' | head -1)

if [ "$STATUS" -ne 0 ]; then
    MENSAJE="❌ *Odín: error en sincronización*%0A📅 $(date '+%d/%m/%Y %H:%M')%0ARevisar /home/k1k3/odin/logs/ingesta/cron_odin.log"
elif [ -z "$NUEVOS" ] || [ "$NUEVOS" -eq 0 ]; then
    MENSAJE="🤖 *Odín: sincronización completada*%0A📅 $(date '+%d/%m/%Y %H:%M')%0ANo hay archivos nuevos en Nextcloud."
else
    MENSAJE="🚀 *Odín: memoria actualizada*%0A📅 $(date '+%d/%m/%Y %H:%M')%0ASe han procesado *$NUEVOS* archivos nuevos o modificados en Qdrant."
fi

# --- ENVIO A TELEGRAM ---
if [ -n "$TOKEN" ] && [ -n "$CHAT_ID" ]; then
    curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
        --data-urlencode "chat_id=${CHAT_ID}" \
        --data-urlencode "text=${MENSAJE}" \
        --data-urlencode "parse_mode=Markdown" > /dev/null
else
    printf '%s\n' "Telegram no configurado; se omite notificacion."
fi

exit "$STATUS"
