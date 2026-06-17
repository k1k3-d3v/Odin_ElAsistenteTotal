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
| Netdata | Activo | Dashboard visual de host, Docker, discos, red y alarmas |
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
http://192.168.1.133:8765/ha_status.json
```

El JSON incluye:

- estado global (`ok`, `warning`, `critical`);
- numero de contenedores, contenedores sin Compose y contenedores no sanos;
- lista de proyectos Docker Compose;
- estado HTTP de Open WebUI, Immich, Qdrant, n8n, Nextcloud y Netdata;
- puntos de la coleccion `memoria_ia` de Qdrant;
- uso de disco de `/` y `/mnt/almacen`;
- resumen de findings de `odin_autorepair.py`.

Estado validado:

| Indicador | Valor |
| --- | --- |
| Servicio HTTP | `odin-health-http.service` activo |
| URL local | `http://127.0.0.1:8765/ha_status.json` |
| URL LAN | `http://192.168.1.133:8765/ha_status.json` |
| Estado global | `ok` |
| Contenedores | 23 |
| Contenedores sin Compose | 0 |
| Contenedores no sanos | 0 |
| Proyectos Compose | 7 |
| Puntos Qdrant | 3554 |

## Dashboard visual

Para monitorizacion visual se ha desplegado Netdata en Docker Compose:

```text
/home/k1k3/odin/monitoring/netdata/docker-compose.yml
```

URL LAN:

```text
http://192.168.1.133:19999
```

Netdata aporta una vista inmediata de CPU, memoria, discos, red, Docker, procesos y alarmas. Es una buena primera capa visual porque no necesita migrar Home Assistant ni tocar la Raspberry Pi 5: Home Assistant sigue viviendo fuera de Docker y Odín solo publica un panel de monitorizacion.

## Dashboard Odín en Home Assistant

El 9 de junio de 2026 se creó un dashboard nativo de Home Assistant que reúne
el estado operativo y los accesos principales:

```text
http://192.168.1.138:8123/odin-panel/resumen
```

El panel aparece en la barra lateral con el nombre `Odín` y contiene cuatro
vistas:

| Vista | Contenido |
| --- | --- |
| Resumen | Estado global, contenedores, avisos, discos, Qdrant y accesos rápidos |
| Servicios | IA, automatización, datos, contenidos, voz, mensajería y vigilancia |
| Casa | Cámara, aspirador, televisión, consolas, móviles, ubicación y tiempo |
| Salud | Health Connect: actividad, sueño, corazón, respiración, oxígeno y composición corporal |
| Organización | Lista de la compra, tareas domésticas y calendario |
| Monitor | Métricas nativas, servicios, discos, avisos y reservas de consumo y backup |

El exportador `odin_ha_status.py` publica 24 entidades mediante la API de Home
Assistant. Incluye sensores agregados y un `binary_sensor` de conectividad por
servicio. El cron existente ejecuta el exportador cada cinco minutos, por lo
que las entidades se vuelven a crear automáticamente después de reiniciar Home
Assistant.

La vista `Salud` utiliza 25 entidades reales sincronizadas desde el Pixel 9 Pro
mediante Health Connect. Presenta pasos, actividad, distancia, calorías, sueño,
frecuencia cardíaca, pulso en reposo, saturación de oxígeno, frecuencia
respiratoria, peso, grasa corporal, masa magra, agua corporal e hidratación.
También conserva visibles las métricas disponibles pero todavía sin datos:
presión arterial, glucosa, variabilidad cardíaca, VO2 máximo y temperaturas
corporales. La salud de la batería y el barómetro del teléfono no se incluyen
porque no son información sanitaria de Health Connect.

Los archivos reproducibles son:

```text
tools/odin_ha_status.py
tools/install_odin_dashboard.py
home-assistant/odin-dashboard.json
```

En el servidor se despliegan en:

```text
/home/k1k3/odin/scripts/odin_ha_status.py
/home/k1k3/odin/scripts/install_odin_dashboard.py
/home/k1k3/odin/dashboard/odin-dashboard.json
```

La credencial de Home Assistant se guarda fuera del repositorio en
`/home/k1k3/odin/scripts/home_assistant.env`, con permisos `0600`.

### Revisión visual

La segunda versión adopta una jerarquía más editorial:

1. Cabecera panorámica propia con estado, contenedores, memoria y avisos.
2. Navegación inmediata hacia Servicios, Casa, Salud y Monitor.
3. Resúmenes contextuales antes de los controles detallados.
4. Imagen y cámaras como elementos principales, no como miniaturas auxiliares.
5. Tarjetas nativas para conservar compatibilidad y mantenimiento sencillo.

Las seis cabeceras se almacenan y se sirven desde el propio Home Assistant:

```text
/api/image/serve/<identificador>/original
```

La inspiración visual se estudió a partir de un dashboard compartido por la
comunidad de Home Assistant, pero la imagen, estructura funcional, entidades y
composición final de Odín son propias.

Cada vista utiliza una imagen diferente:

| Vista | Tema visual |
| --- | --- |
| Resumen | Servidor doméstico integrado en un despacho |
| Servicios | Infraestructura y racks |
| Casa | Interior residencial |
| Salud | Actividad y dispositivo de salud |
| Organización | Checklist y planificación |
| Monitor | Estación de trabajo y panel de control |

Los originales procesados y sus atribuciones se conservan en
`home-assistant/assets/views/`. Las copias utilizadas en producción están
subidas al almacén de imágenes de Home Assistant.

Todas las vistas comparten dimensiones y tratamiento visual, pero no la
fotografía: cada dominio tiene su propia cabecera temática. La vista Salud usa
además `mdi:heart-pulse` tanto en la navegación como en sus accesos principales.
Los títulos superpuestos usan la tipografía principal de Home Assistant con
peso 600 y un tamaño máximo contenido, siguiendo la jerarquía compacta de la
referencia visual y evitando el aspecto excesivamente fino de la primera
versión.
Cada vista conserva la cuadrícula adecuada a su contenido: Resumen utiliza
cuatro columnas, Casa tres y Servicios, Salud, Organización y Monitor dos.
Las cabeceras ocupan siempre el ancho disponible de su propia vista y los
controles mantienen sus dimensiones originales.

La cabecera de Salud es una imagen propia generada para el proyecto. Representa
un entorno doméstico sereno con reloj inteligente y pulsioxímetro, sin personas
ni estética deportiva, y reserva espacio oscuro a la izquierda para el título.

La vista Casa reúne también el uso cotidiano del hogar. Incluye controles para
Google TV, la televisión del salón y Xbox Series X; un mapa de los móviles
Pixel 9 Pro e iPhone de Ivet; sus niveles de batería y ubicaciones geocodificadas;
y la previsión diaria de `weather.forecast_casa`. Se han utilizado únicamente
entidades existentes, priorizando las que responden actualmente para no llenar
el panel con integraciones antiguas en estado `unavailable`.

La vista Monitor no contiene iframes. Esto evita solicitudes de inicio de
sesión adicionales, contenido mixto y bloqueos de Private Network Access al
abrir Home Assistant desde una URL pública. Netdata permanece como un botón
opcional para uso directo dentro de la LAN.

Los espacios de ampliación ya existen como entidades:

```text
sensor.odin_consumo_servidor
sensor.odin_consumo_auxiliar
sensor.odin_backup_estado
sensor.odin_backup_ultima_copia
sensor.odin_backup_tamano
```

Los enchufes Sonoff de la torre y la Raspberry Pi ya sustituyen las reservas
de consumo. La vista Monitor muestra potencia instantánea, energía diaria y
mensual, dos gráficas históricas y coste acumulado estimado con una tarifa
inicial de `0,20 €/kWh`. Los contadores totales deshabilitados por Sonoff se
han activado y el cálculo los prioriza cuando proporcionan una lectura válida.

Cuando se configure el NVMe, las entidades de backup se
alimentarán con datos reales sin rediseñar el panel.

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

Segun la documentacion oficial, Home Assistant puede consumir endpoints JSON mediante la integracion RESTful Sensor, que realiza peticiones GET periodicas a un recurso HTTP. Ejemplo base para sensores:

```yaml
sensor:
  - platform: rest
    name: Odin Estado
    resource: http://192.168.1.133:8765/ha_status.json
    value_template: "{{ value_json.overall }}"
    json_attributes:
      - docker
      - endpoints
      - disk
      - qdrant_points
      - autorepair
    scan_interval: 60
```

Durante la primera iteración se probó una tarjeta Webpage/iframe:

```yaml
type: iframe
url: http://192.168.1.133:19999
aspect_ratio: 75%
title: Odin Monitor
```

Esta alternativa quedó retirada del dashboard final. Cuando Home Assistant se
abre por HTTPS, el navegador puede bloquear el iframe HTTP por contenido mixto
o por Private Network Access. La versión vigente muestra métricas nativas y
deja Netdata como botón externo para uso en la LAN.

Fuentes:

- Home Assistant RESTful Sensor: https://www.home-assistant.io/integrations/sensor.rest/
- Home Assistant Command Line integration: https://www.home-assistant.io/integrations/command_line/
- Home Assistant Webpage card: https://www.home-assistant.io/dashboards/iframe/
- Netdata Docker installation: https://learn.netdata.cloud/docs/netdata-agent/installation/docker
