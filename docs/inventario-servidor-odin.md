# Inventario inicial del servidor Odín

Fecha de inspección: 2026-05-07  
Host: `odin`  
Usuario: `k1k3`  
Sistema: Ubuntu 24.04.4 LTS  
Kernel: Linux 6.18.7  
Hardware detectado: ASRock A520M-HVS, AMD Ryzen 5 5600G, GPU AMD Radeon RX 9070/9070 XT/GRE, 30 GiB RAM.

> Documento de trabajo sin secretos. No incluye valores de `.env`, claves, tokens ni credenciales.

## Almacenamiento

| Punto | Tamaño | Uso aproximado | Comentario |
| --- | ---: | ---: | --- |
| `/` | 914 GB | 80% | Sistema principal y servicios |
| `/mnt/almacen` | 880 GB | 24% | Almacenamiento auxiliar/backups |
| `/boot` | 2 GB | 18% | Arranque |

## Aceleración IA

ROCm está instalado y detecta la GPU.

Estado observado:

| Métrica | Valor |
| --- | ---: |
| GPU use | 3% |
| VRAM usada | 0% |
| Temperatura edge | 38 C |
| Temperatura junction | 40 C |
| Temperatura memory | 40 C |

Nota: el mensaje de bienvenida del sistema muestra una temperatura absurda (`3892314.0 C`), probablemente por lectura incorrecta de sensor. Para la memoria conviene usar `rocm-smi` como fuente fiable.

## Proyectos principales

| Ruta | Función probable |
| --- | --- |
| `/home/k1k3/odin` | Estructura actual modular del ecosistema Odín |
| `/home/k1k3/odin-master` | Compose principal con servicios core |
| `/home/k1k3/odin-ia` | Servicios o pruebas de IA |
| `/home/k1k3/odin-asr-models` | Modelos ASR |
| `/home/k1k3/cuarentena` | Pruebas, backups y experimentos descartados o aislados |

## Estructura `/home/k1k3/odin`

| Carpeta | Contenido observado |
| --- | --- |
| `audio/` | ASR, Whisper, Piper, PocketTTS y configuración de voz |
| `automation/frigate/` | Frigate para cámaras y detección |
| `core/` | Servicios core y Open WebUI |
| `data/` | Datos persistentes de Open WebUI |
| `media/immich-app/` | Immich y machine learning asociado |
| `scripts/` | Automatizaciones de backup, ingesta y actualización |

## Docker Compose

Proyectos Compose activos detectados:

| Proyecto | Estado | Compose |
| --- | --- | --- |
| `audio` | running(4) | `/home/k1k3/odin/audio/docker-compose.yml` |
| `frigate` | running(1) | `/home/k1k3/odin/automation/frigate/docker-compose.yml` |
| `immich` | running(4) | `/home/k1k3/odin/media/immich-app/docker-compose.yml` |
| `odin-master` | running(10) | `/home/k1k3/odin-master/docker-compose.yml` |
| `pocket-tts-openai_streaming_server` | running(1) | `/home/k1k3/odin/audio/pocket-tts-openai_streaming_server/docker-compose.yml` |

## Contenedores activos

| Contenedor | Imagen | Función |
| --- | --- | --- |
| `frigate` | `ghcr.io/blakeblackshear/frigate:stable` | Cámaras, vigilancia y detección |
| `pockettts-server` | `pockettts-openai-server:latest` | TTS compatible con estilo OpenAI |
| `immich_server` | `ghcr.io/immich-app/immich-server:v2` | Gestión de fotos/vídeos |
| `immich_postgres` | `ghcr.io/immich-app/postgres:14-vectorchord...` | Base de datos Immich |
| `immich_machine_learning` | `ghcr.io/immich-app/immich-machine-learning:v2-rocm` | ML de Immich con ROCm |
| `immich_redis` | `valkey/valkey:9` | Cache/cola Immich |
| `piper` | `lscr.io/linuxserver/piper:latest` | Síntesis de voz |
| `faster-whisper-server` | `fedirz/faster-whisper-server:latest-cpu` | ASR Whisper en CPU |
| `odin-asr` | `odin-onnx-asr` | ASR propio en ONNX |
| `wyoming-whisper` | `rhasspy/wyoming-whisper` | Integración Whisper/Wyoming |
| `crawl4ai` | `unclecode/crawl4ai:latest` | Ingesta/búsqueda web |
| `n8n-odin` | `n8nio/n8n` | Orquestación de flujos |
| `webui-odin` | `ghcr.io/open-webui/open-webui:main` | Interfaz LLM |
| `nextcloud-odin` | `nextcloud:latest` | Nube privada |
| `evolution-odin` | `atendai/evolution-api:latest` | Integración de mensajería |
| `evolution-db` | `postgres:15-alpine` | Base de datos Evolution API |
| `redis-odin` | `redis:alpine` | Redis compartido |
| `qdrant-odin` | `qdrant/qdrant:latest` | Base vectorial para RAG |
| `nextcloud-db` | `mariadb:10.11` | Base de datos Nextcloud |
| `cloudflared-odin` | `cloudflare/cloudflared:latest` | Túnel Cloudflare |
| `ha-proxy` | `alpine/socat` | Proxy hacia Home Assistant |

Contenedores detenidos observados:

| Contenedor | Imagen | Estado |
| --- | --- | --- |
| `stirling-pdf` | `stirlingtools/stirling-pdf:latest` | Exited |
| `festive_almeida` | `ghcr.io/remsky/kokoro-fastapi-cpu:latest` | Exited |
| `thirsty_hamilton` | `ghcr.io/remsky/kokoro-fastapi-cpu:latest` | Exited |

## Puertos publicados en LAN/VPN

| Puerto | Servicio probable |
| ---: | --- |
| 22 | SSH |
| 2283 | Immich |
| 5001 | Frigate UI/API interna publicada |
| 5002 | Odin ASR |
| 5679 | n8n |
| 6333 | Qdrant |
| 8082 | Nextcloud |
| 8085 | Evolution API |
| 8123 | Home Assistant proxy |
| 8554/8555 | Frigate RTSP/WebRTC |
| 8971 | Frigate |
| 10200 | Piper |
| 10300 | Wyoming Whisper |
| 10301 | Faster Whisper |
| 11235 | crawl4ai |
| 49112 | PocketTTS |

## Automatizaciones cron

```cron
*/30 * * * * /home/k1k3/env/bin/python3 /home/k1k3/update_odin.py >> /home/k1k3/odin_sync.log 2>&1
0 * * * * /home/k1k3/lanzar_ingesta.sh >> /home/k1k3/odin_sync.log 2>&1
```

Hay scripts equivalentes dentro de `/home/k1k3/odin/scripts/`, por lo que conviene revisar si las rutas del cron son versiones antiguas o wrappers.

## Correspondencia con el mapa funcional

| Bloque | Evidencia actual |
| --- | --- |
| Hacer | n8n, Nextcloud, Home Assistant proxy, scripts de ingesta/actualización, crawl4ai |
| Pensar | Open WebUI, Qdrant, crawl4ai, Immich, datos persistentes de WebUI |
| Proactivo | Frigate, cron de actualización/ingesta, scripts de backup, Immich auto-upload, monitorización GPU posible con ROCm |
| Otros | Dashboard pendiente de consolidar, limpieza de caché pendiente de formalizar, voz soportada por ASR/TTS/Wyoming/Piper |

## Riesgos y notas inmediatas

- El sistema raíz está al 80% de uso. Conviene documentar política de limpieza, backups y separación de datos.
- Hay servicios publicados en `0.0.0.0`; al estar dentro de LAN/VPN puede ser aceptable, pero para la memoria debe justificarse la ausencia de exposición directa a Internet.
- Hay varios experimentos en `cuarentena`; son material valioso para el capítulo de problemas encontrados y alternativas descartadas.
- El stack de voz está bastante rico: Whisper CPU, Wyoming Whisper, ASR ONNX propio, Piper y PocketTTS.
- Immich con machine learning ROCm es una evidencia fuerte para el bloque de fotos y búsqueda visual.
- Qdrant y Open WebUI sostienen la narrativa de memoria/RAG.
