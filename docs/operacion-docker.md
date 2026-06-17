# Operacion Docker de Odin

Fecha: 2026-05-11

Documento de trabajo sin secretos. No incluye valores de `.env`, tokens ni claves.

## Objetivo

La organizacion actual se basa en separar los contenedores por dominio funcional. No todos los servicios nacieron al mismo tiempo, por lo que todavia conviven stacks ordenados con alguna pieza historica. La prioridad inmediata es documentar lo que existe y evitar cambios destructivos.

## Stacks Compose activos

| Stack | Ruta | Servicios | Funcion |
| --- | --- | ---: | --- |
| `odin-master` | `/home/k1k3/odin/core/odin-master/docker-compose.yml` | 11 | Open WebUI, Qdrant, Nextcloud, n8n, Evolution API, Cloudflared, Crawl4AI y Stirling PDF |
| `immich` | `/home/k1k3/odin/media/immich-app/docker-compose.yml` | 4 | Fotos, base de datos, Redis y machine learning de Immich |
| `audio` | `/home/k1k3/odin/audio/docker-compose.yml` | 4 | Piper, faster-whisper, Wyoming Whisper y ASR propio |
| `frigate` | `/home/k1k3/odin/automation/frigate/docker-compose.yml` | 1 | Videovigilancia y deteccion de personas |
| `home-assistant-proxy` | `/home/k1k3/odin/automation/home-assistant-proxy/docker-compose.yml` | 1 | Proxy local hacia Home Assistant |
| `netdata` | `/home/k1k3/odin/monitoring/netdata/docker-compose.yml` | 1 | Monitorizacion visual de Odín |
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
| Monitorizacion | `netdata` |
| Utilidades | `stirling-pdf` |

## Reorganizacion ejecutada

Se movio el stack principal desde `/home/k1k3/odin-master` a:

```text
/home/k1k3/odin/core/odin-master
```

Para reducir riesgo se mantuvo un enlace simbolico de compatibilidad:

```text
/home/k1k3/odin-master -> /home/k1k3/odin/core/odin-master
```

Open WebUI recibio atencion especial. Antes del cambio, el contenedor montaba sus datos desde `/home/k1k3/openweb_ui_data`, una ruta externa al arbol principal. Se verifico que el contenido ya existia en `/home/k1k3/odin/data/openweb_ui_data`, se actualizo el compose para usar esa ruta y se dejo el camino antiguo como enlace simbolico de compatibilidad:

```text
/home/k1k3/openweb_ui_data -> /home/k1k3/odin/data/openweb_ui_data
```

Tambien se incorporo `ha-proxy` a Docker Compose. Antes era un contenedor creado manualmente, sin etiquetas Compose; ahora pertenece al stack `home-assistant-proxy`. Home Assistant no se ha levantado en Docker en Odín: sigue alojado en la Raspberry Pi 5, y `ha-proxy` actua solo como puente HTTP local.

Para la monitorizacion visual se desplego Netdata en `/home/k1k3/odin/monitoring/netdata`. El servicio escucha en `http://192.168.1.133:19999` y puede integrarse en Home Assistant mediante una tarjeta Webpage/iframe, sin modificar la instalacion principal de HA.

## Estado observado

Todos los contenedores activos aparecen en estado `Up`. Los contenedores principales que exponen healthcheck (`immich`, `webui`, `crawl4ai`, `frigate`, `stirling-pdf`, `pockettts`) aparecen como `healthy`.

Validacion final:

| Indicador | Valor |
| --- | ---: |
| Contenedores totales | 23 |
| Contenedores sin Compose | 0 |
| Contenedores no sanos | 0 |
| Proyectos Compose activos | 7 |

Puntos a vigilar:

- `odin-master` concentra demasiadas responsabilidades; para memoria y mantenimiento seria mas claro separar `core`, `automation`, `storage` y `ingestion`.
- Hay secretos historicos incrustados en compose y scripts antiguos. La direccion correcta es moverlos a `.env` y no versionarlos.
- Se eliminaron redes Docker sin contenedores asociadas a pruebas antiguas.
- Los volumenes Docker no se han eliminado porque pueden contener datos o caches utiles.

## Validacion posterior

| Servicio | Comprobacion | Resultado |
| --- | --- | --- |
| Open WebUI | `http://127.0.0.1:3000/health` | `200` |
| Qdrant | `http://127.0.0.1:6333/collections/memoria_ia` | `200`, coleccion `green` |
| Nextcloud | `http://127.0.0.1:8082/` | `302` |
| n8n | `http://127.0.0.1:5679/` | `200` |
| Immich | `http://127.0.0.1:2283/api/server/ping` | `200` |
| Netdata | `http://127.0.0.1:19999/api/v1/info` | `200` |
| Stirling PDF | `http://127.0.0.1:8080/` | `401`, servicio activo con autenticacion |

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
| `/home/k1k3/odin/monitoring` | Netdata, exportadores y futuras herramientas de observabilidad |
| `/home/k1k3/odin/scripts` | Cron, ingesta, autoreparacion, backups y herramientas auxiliares |
| `/home/k1k3/odin/docs` | Inventario operativo, decisiones tecnicas y runbooks |

La reorganizacion debe hacerse por fases: primero documentar, despues mover secretos a `.env`, luego separar compose sin cambiar volumenes, y finalmente limpiar carpetas historicas. El primer paso ya queda completado: los stacks Docker activos estan bajo `/home/k1k3/odin` o sus subcarpetas.
