# Monitorizacion de Odin para Home Assistant

Fecha: 2026-05-11

Documento sin secretos. El endpoint expone estado operativo, no credenciales.

## Estado actual

Odín cuenta con varias capas de monitorizacion:

| Capa | Estado | Comentario |
| --- | --- | --- |
| `odin_autorepair.py` | Activo por cron | Diagnostica Ollama, GPU, Docker, disco, cron y Qdrant |
| Telegram | Activo | Alertas ante cambios y reporte diario |
| `smartmontools` | Activo | Monitorizacion SMART de discos |
| `lm-sensors` | Disponible | Temperaturas de GPU, CPU, NVMe y placa |
| Docker healthchecks | Parcial | Open WebUI, Immich, Frigate, Crawl4AI, PocketTTS y Stirling PDF reportan `healthy` |
| `odin-monitor.service` antiguo | Desactivado | Estaba en auto-restart fallando por script inexistente |

Tambien existen servicios systemd antiguos relacionados con voz (`odin-asr.service`, `odin-stt-proxy.service`, `whisper-odin.service`) que aparecen fallidos o reiniciando. No forman parte del estado Docker actual y deben revisarse antes de borrarlos.

## Endpoint compatible con Home Assistant

Se ha creado un exportador local:

```text
/home/k1k3/odin/scripts/odin_ha_status.py
```

Genera:

```text
/home/k1k3/odin/public/ha_status.json
```

Y se sirve por HTTP en:

```text
http://192.168.86.105:8765/ha_status.json
```

El JSON incluye:

- estado global (`ok`, `warning`, `critical`);
- numero de contenedores, contenedores sin Compose y contenedores no sanos;
- lista de proyectos Docker Compose;
- estado HTTP de Open WebUI, Immich, Qdrant, n8n y Nextcloud;
- puntos de la coleccion `memoria_ia` de Qdrant;
- uso de disco de `/` y `/mnt/almacen`;
- resumen de findings de `odin_autorepair.py`.

Estado validado:

| Indicador | Valor |
| --- | --- |
| Servicio HTTP | `odin-health-http.service` activo |
| URL local | `http://127.0.0.1:8765/ha_status.json` |
| URL LAN | `http://192.168.86.105:8765/ha_status.json` |
| Estado global | `ok` |
| Contenedores | 22 |
| Contenedores sin Compose | 0 |
| Contenedores no sanos | 0 |
| Proyectos Compose | 6 |
| Puntos Qdrant | 3554 |

## Cron

El exportador se ejecuta cada cinco minutos:

```cron
*/5 * * * * /home/k1k3/odin/scripts/odin_ha_status.py >> /home/k1k3/odin/logs/health/ha_status.log 2>&1
```

## Servicio HTTP

El JSON se publica mediante systemd:

```text
/etc/systemd/system/odin-health-http.service
```

Plantilla versionada en el repositorio:

```text
server-systemd/odin-health-http.service
```

## Ejemplo Home Assistant

Segun la documentacion oficial, Home Assistant puede consumir endpoints JSON mediante la integracion RESTful Sensor, que realiza peticiones GET periodicas a un recurso HTTP. Ejemplo base:

```yaml
sensor:
  - platform: rest
    name: Odin Estado
    resource: http://192.168.86.105:8765/ha_status.json
    value_template: "{{ value_json.overall }}"
    json_attributes:
      - docker
      - endpoints
      - disk
      - qdrant_points
      - autorepair
    scan_interval: 60
```

Fuentes:

- Home Assistant RESTful Sensor: https://www.home-assistant.io/integrations/sensor.rest/
- Home Assistant Command Line integration: https://www.home-assistant.io/integrations/command_line/
