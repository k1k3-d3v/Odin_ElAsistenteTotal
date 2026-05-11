# Catalogo de codigo y fuentes para la memoria

Fecha: 2026-05-11

Este documento organiza que fragmentos de codigo conviene incluir en la memoria y que fuentes tecnicas deben citarse. No contiene secretos ni valores reales de `.env`.

## Candidatos de codigo

| Bloque | Archivo / origen | Incluir en memoria | Motivo |
| --- | --- | --- | --- |
| Cron de ingesta | `tools/cron_odin_ingesta.sh` | Si | Muestra automatizacion real, logs, control de errores y Telegram sin exponer secretos |
| Autoreparabilidad | `tools/odin_autorepair.py` | Si, fragmentos | Es una aportacion propia fuerte: diagnostico, alertas y reparacion conservadora |
| Open WebUI + Qdrant | Compose real del servidor, version saneada | Si, fragmento | Explica el nucleo conversacional y la memoria vectorial |
| Immich | Compose real del servidor, version saneada | Si, fragmento | Muestra uso de almacenamiento externo y ML con ROCm |
| Audio/STT/TTS | `/home/k1k3/odin/audio/docker-compose.yml`, saneado | Si, tabla o fragmento | Resume Piper, Whisper, Wyoming y ASR propio |
| Home Assistant proxy | `server-compose/home-assistant-proxy/docker-compose.yml` | Si | Ejemplo pequeno, limpio y sin secretos |
| Netdata | `server-compose/netdata/docker-compose.yml` | Si | Dashboard visual de monitorizacion compatible con Home Assistant |
| Frigate | Compose/config saneado | Tal vez | Util si se explica deteccion de personas y decision CPU/GPU |
| Open WebUI tools | Export/snapshot saneado de tools | Si, varios fragmentos pequenos | Es lo que diferencia a Odin: acciones reales desde el chat |
| Ingesta master | `odin_ingesta_master.py`, fragmentos | Si | Explica RAG local: extraccion, chunking, embeddings y Qdrant |

## Fuentes tecnicas principales

| Tema | Fuente recomendada |
| --- | --- |
| Docker Compose | https://docs.docker.com/reference/compose-file/ |
| Volumenes en Compose | https://docs.docker.com/reference/compose-file/volumes/ |
| Open WebUI Tools | https://docs.openwebui.com/features/extensibility/plugin/tools/ |
| Open WebUI Functions | https://docs.openwebui.com/features/extensibility/plugin/functions/ |
| Immich con Docker Compose | https://docs.immich.app/install |
| Requisitos de Immich | https://docs.immich.app/install/requirements/ |
| Qdrant storage | https://qdrant.tech/documentation/manage-data/storage/ |
| n8n con Docker | https://docs.n8n.io/hosting/installation/docker/ |
| Frigate installation | https://docs.frigate.video/frigate/installation |
| Tailscale y WireGuard | https://tailscale.com/docs/concepts/what-is-tailscale |
| Tailscale con IP dinamica | https://tailscale.com/docs/reference/wireguard-dynamic-ip |
| Netdata en Docker | https://learn.netdata.cloud/docs/netdata-agent/installation/docker |
| Home Assistant Webpage card | https://www.home-assistant.io/dashboards/iframe/ |

## Criterio para elegir fragmentos

No conviene pegar archivos completos. Para la memoria interesa mostrar piezas pequenas que demuestren decisiones tecnicas:

- montaje persistente de datos;
- separacion de secretos con `.env`;
- healthchecks y reinicio automatico;
- uso de GPU/ROCm cuando aplica;
- automatizaciones con logs y control de errores;
- integracion entre Open WebUI, Qdrant, Nextcloud, Home Assistant e Immich.

## Pendiente

- Crear versiones saneadas de los compose con contrasenas, tokens y dominios sensibles sustituidos.
- Exportar o copiar solo las tools de Open WebUI que sean representativas.
- Asociar cada fragmento a un requisito funcional o no funcional de la memoria.
- Convertir estas fuentes en entradas BibTeX dentro de `references.bib`.
