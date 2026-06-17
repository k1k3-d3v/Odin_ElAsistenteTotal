# Diagnóstico de Ollama y autoreparabilidad

Fecha: 2026-05-07  
Servidor: `odin`

## Estado inicial

Ollama estaba instalado como servicio systemd:

- unidad: `ollama.service`;
- binario: `/usr/local/bin/ollama`;
- usuario de ejecución: `ollama`;
- host expuesto por configuración: `OLLAMA_HOST=0.0.0.0`;
- variable ROCm: `HSA_OVERRIDE_GFX_VERSION=12.0.0`.

En la inspección inicial el servicio estaba parado:

```text
Active: inactive (dead) since Wed 2026-05-06 21:10:52 UTC
```

El servicio se había detenido limpiamente por systemd:

```text
Stopping ollama.service - Ollama Service...
Deactivated successfully.
Stopped ollama.service.
```

## Causa probable de los fallos previos

Antes de la parada limpia del servicio, los logs muestran varias caídas del runner del modelo:

```text
llama runner terminated error="signal: killed"
```

La lectura más probable es presión o inestabilidad en GPU/ROCm, no una caída completa del servicio principal. Las pistas son:

- Ollama detectaba la AMD Radeon RX 9070 vía ROCm.
- El modelo cargado ocupaba aproximadamente `10.0 GiB`.
- Tras las caídas del runner, Ollama veía solo unos `4.9 GiB` libres de VRAM sobre un total de unos `17.1 GiB`.
- El kernel registra muchas evacuaciones de colas AMDGPU:

```text
amdgpu: Freeing queue vital buffer ..., queue evicted
```

También aparece repetidamente:

```text
rocblaslt error: Cannot read "TensileLibrary_lazy_gfx1200.dat"
rocblaslt error: Could not load "TensileLibrary_lazy_gfx1200.dat"
```

Este aviso no impidió siempre que el modelo arrancara, pero sí es una señal relevante de fricción entre Ollama, ROCm y la arquitectura `gfx1200/gfx1201`.

Además, los logs muestran prompts truncados:

```text
truncating input prompt limit=4096
```

Esto no explica por sí solo la caída, pero sí indica que algunos flujos estaban enviando contexto por encima de la ventana configurada.

## Acción realizada

Se levantó Ollama con systemd:

```bash
sudo systemctl start ollama
```

Después del arranque:

```text
systemctl is-active ollama -> active
GET /api/tags -> OK
```

Modelos detectados mediante API:

- `gemma4:e4b`, Q4_K_M, aproximadamente 9.6 GB en disco;
- `mxbai-embed-large:latest`, modelo de embeddings.

## Herramienta creada

Se creó una herramienta conservadora de autoreparabilidad:

```text
/home/k1k3/odin/scripts/odin_autorepair.py
```

También está versionada en el repositorio:

```text
tools/odin_autorepair.py
```

El 2026-05-07 se amplió para enviar informes por Telegram reutilizando el `TOKEN` y el `CHAT_ID` ya existentes en los scripts de cron del servidor. Estos secretos no se versionan en el repositorio.

## Qué comprueba

- Estado de `ollama.service`.
- Disponibilidad de la API local de Ollama (`/api/tags`).
- Patrones de fallo en `journalctl -u ollama`.
- Eventos de kernel relacionados con AMDGPU.
- Estado de GPU mediante `rocm-smi`.
- Estado de contenedores importantes.
- Uso de disco en `/` y `/mnt/almacen`.
- Estado de rutas referenciadas por `crontab`.
- Logs de ingesta y sincronización.
- Estado de la colección `memoria_ia` en Qdrant.

## Política de reparación

Por defecto solo diagnostica:

```bash
/home/k1k3/odin/scripts/odin_autorepair.py
```

En modo reparación:

```bash
/home/k1k3/odin/scripts/odin_autorepair.py --repair
```

Acciones permitidas:

- Si Ollama está inactivo, intenta arrancarlo con `sudo -n systemctl start ollama`.
- No reinicia contenedores automáticamente.
- No reinicia Ollama si está activo salvo que se use explícitamente `--restart-ollama`.

Esto evita que la autoreparación sea más peligrosa que el fallo original.

## Resultado de prueba

La herramienta se ejecutó en modo diagnóstico y reparación. Como Ollama ya estaba activo y la API respondía, el modo reparación no ejecutó acciones:

```text
actions: []
ollama_active: true
api_ok: true
post_api_ok: true
```

La herramienta escribe informes JSON en:

```text
/home/k1k3/odin/logs/autorepair/
```

## Informes por Telegram

La herramienta soporta dos modos de notificación:

```bash
/home/k1k3/odin/scripts/odin_autorepair.py --daily
/home/k1k3/odin/scripts/odin_autorepair.py --repair --alert
```

El informe diario se envía siempre e incluye:

- resumen de críticos, avisos e información;
- estado de Ollama, GPU, Docker, cron, disco y Qdrant;
- qué hay de malo;
- qué hay de nuevo según logs de ingesta;
- fuentes revisadas/visitadas;
- fuentes de memoria procesadas recientemente.

El formato se actualizó a HTML de Telegram para mejorar la lectura en móvil: encabezado de estado general, secciones por bloques, severidades con iconos y fuentes en formato monoespaciado.

El modo alerta solo envía mensaje si hay problemas `warning` o `critical` y si la firma del problema ha cambiado respecto al último aviso, evitando spam repetitivo.

## Cron corregido

Se detectó que el cron antiguo apuntaba a rutas que ya no existían:

```text
/home/k1k3/update_odin.py
/home/k1k3/lanzar_ingesta.sh
/home/k1k3/cron_odin_ingesta.sh
```

Se actualizó el crontab a rutas reales dentro de `/home/k1k3/odin/scripts/` y se añadió reporte/autoreparación:

```cron
*/30 * * * * /home/k1k3/env/bin/python3 /home/k1k3/odin/scripts/update_odin.py >> /home/k1k3/odin_sync.log 2>&1
0 * * * * /home/k1k3/odin/scripts/lanzar_ingesta.sh >> /home/k1k3/odin_sync.log 2>&1
*/15 * * * * /home/k1k3/odin/scripts/odin_autorepair.py --repair >> /home/k1k3/odin/logs/autorepair/cron.log 2>&1
45 7 * * * /home/k1k3/odin/scripts/odin_autorepair.py --daily >> /home/k1k3/odin/logs/autorepair/cron.log 2>&1
```

Antes de modificar el cron se guardó una copia en `/home/k1k3/odin/logs/autorepair/`.

## Conclusión para la memoria

Este caso representa un ejemplo claro de autoreparabilidad pragmática: el sistema no intenta "curarse" de forma ciega, sino observar su estado, clasificar síntomas y ejecutar únicamente reparaciones seguras. Para Odín, esto es especialmente importante porque conviven servicios críticos, GPU compartida, contenedores y herramientas experimentales.
