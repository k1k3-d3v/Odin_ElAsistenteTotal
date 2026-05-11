# Operacion Docker de Odin

Fecha: 2026-05-11

Documento de trabajo sin secretos. No incluye valores de `.env`, tokens ni claves.

## Objetivo

La organizacion actual se basa en separar los contenedores por dominio funcional. No todos los servicios nacieron al mismo tiempo, por lo que todavia conviven stacks ordenados con alguna pieza historica. La prioridad inmediata es documentar lo que existe y evitar cambios destructivos.

## Stacks Compose activos

| Stack | Ruta | Servicios | Funcion |
| --- | --- | ---: | --- |
| `odin-master` | `/home/k1k3/odin-master/docker-compose.yml` | 11 | Open WebUI, Qdrant, Nextcloud, n8n, Evolution API, Cloudflared, Crawl4AI y Stirling PDF |
| `immich` | `/home/k1k3/odin/media/immich-app/docker-compose.yml` | 4 | Fotos, base de datos, Redis y machine learning de Immich |
| `audio` | `/home/k1k3/odin/audio/docker-compose.yml` | 4 | Piper, faster-whisper, Wyoming Whisper y ASR propio |
| `frigate` | `/home/k1k3/odin/automation/frigate/docker-compose.yml` | 1 | Videovigilancia y deteccion de personas |
| `pocket-tts-openai_streaming_server` | `/home/k1k3/odin/audio/pocket-tts-openai_streaming_server/docker-compose.yml` | 1 | TTS compatible con API estilo OpenAI |

## Contenedores por area

| Area | Contenedores |
| --- | --- |
| Interfaz e IA | `webui-odin`, `qdrant-odin`, `crawl4ai`, `ollama.service` fuera de Docker |
| Memoria y archivos | `nextcloud-odin`, `nextcloud-db`, `qdrant-odin` |
| Fotos | `immich_server`, `immich_postgres`, `immich_redis`, `immich_machine_learning` |
| Voz | `piper`, `faster-whisper-server`, `wyoming-whisper`, `odin-asr`, `pockettts-server` |
| Automatizacion | `n8n-odin`, `evolution-odin`, `evolution-db`, `redis-odin` |
| Seguridad/acceso | `cloudflared-odin`, `ha-proxy`, Tailscale fuera de Docker |
| Camaras | `frigate` |
| Utilidades | `stirling-pdf` |

## Estado observado

Todos los contenedores activos aparecen en estado `Up`. Los contenedores principales que exponen healthcheck (`immich`, `webui`, `crawl4ai`, `frigate`, `stirling-pdf`, `pockettts`) aparecen como `healthy`.

Puntos a vigilar:

- `ha-proxy` aparece sin etiqueta Compose, por lo que conviene integrarlo en un compose versionado o documentar claramente su creacion manual.
- `odin-master` concentra demasiadas responsabilidades; para memoria y mantenimiento seria mas claro separar `core`, `automation`, `storage` y `ingestion`.
- Hay secretos historicos incrustados en compose y scripts antiguos. La direccion correcta es moverlos a `.env` y no versionarlos.
- Existen redes Docker antiguas o de pruebas, como `parakeet-tdt-06b-v3-fastapi-openai_default`, que se deben revisar antes de borrar.
- Los volumenes Docker no se han eliminado porque pueden contener datos o caches utiles.

## Politica de limpieza

Acciones seguras ejecutadas:

- `docker container prune -f`;
- `docker builder prune -af`;
- `docker image prune -af`.

Acciones evitadas:

- `docker system prune --volumes`;
- borrado de `/home/k1k3/cuarentena`;
- borrado del origen antiguo de Immich en `/home/k1k3/Pictures/immich`;
- borrado de caches de modelos sin inventario.

## Propuesta de organizacion futura

| Carpeta | Contenido propuesto |
| --- | --- |
| `/home/k1k3/odin/core` | Open WebUI, Qdrant, Crawl4AI y configuracion del nucleo |
| `/home/k1k3/odin/storage` | Nextcloud, Immich, bases de datos y politica de almacenamiento |
| `/home/k1k3/odin/audio` | STT, ASR, TTS y satelites de voz |
| `/home/k1k3/odin/automation` | n8n, Home Assistant bridge, Evolution API y Frigate |
| `/home/k1k3/odin/scripts` | Cron, ingesta, autoreparacion, backups y herramientas auxiliares |
| `/home/k1k3/odin/docs` | Inventario operativo, decisiones tecnicas y runbooks |

La reorganizacion debe hacerse por fases: primero documentar, despues mover secretos a `.env`, luego separar compose sin cambiar volumenes, y finalmente limpiar carpetas historicas.
