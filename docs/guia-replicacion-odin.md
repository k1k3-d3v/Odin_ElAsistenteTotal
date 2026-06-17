# Guía detallada para replicar el proyecto Odín

Versión documental: 2026-06-09

## 1. Propósito y alcance

Esta guía permite reconstruir una instalación funcional inspirada en el
servidor Odín a partir de los artefactos saneados de este repositorio. No es una
imagen del sistema ni un instalador automático. Odín integra datos personales,
tokens, cámaras, dispositivos domóticos y decisiones dependientes del hardware;
por tanto, una réplica responsable exige configurar cada frontera de seguridad.

La guía ofrece dos niveles:

1. **Réplica mínima:** Ollama, Open WebUI, Qdrant, Nextcloud, n8n y
   monitorización.
2. **Réplica completa:** añade Immich, Home Assistant, Frigate, voz, Mealie,
   ingesta documental, tools y proxies visuales.

El resultado esperado es una arquitectura local-first donde el modelo no
accede directamente a todos los servicios. Open WebUI expone tools limitadas;
los proxies encapsulan tokens y las acciones físicas se delegan en Home
Assistant.

## 2. Qué no incluye el repositorio

Por seguridad no se incluyen:

- contraseñas, API keys, tokens o cookies;
- configuración RTSP real de cámaras;
- certificados, claves SSH ni credenciales de Tailscale;
- datos de Nextcloud, Immich, Mealie o Qdrant;
- token de larga duración de Home Assistant;
- configuración privada de n8n;
- modelos ASR propios o voces con posibles restricciones;
- contenido de las bases SQLite operativas de Open WebUI y Mealie.

No deben copiarse secretos desde otra instalación. Cada réplica debe generar los
suyos.

## 3. Arquitectura objetivo

```text
Clientes LAN/VPN
       |
       +-- Open WebUI :3000 -------- Ollama :11434
       |        |
       |        +-- Qdrant :6333
       |        +-- Tools Python
       |              |
       |              +-- Home Assistant :8123
       |              +-- Frigate :5001
       |              +-- Immich proxy :2290
       |              +-- Nextcloud proxy :2291
       |              +-- Mealie proxy :2292
       |              +-- Frigate image proxy :2293
       |
       +-- Nextcloud :8082
       +-- Immich :2283
       +-- Mealie :9925
       +-- n8n :5679
       +-- Netdata :19999
       +-- Frigate :8971 / RTSP :8554
```

Home Assistant puede ejecutarse en otra máquina, como una Raspberry Pi. En ese
caso, un proxy local opcional publica su API en el servidor Odín. Si Home
Assistant comparte host con las tools, puede usarse su URL directamente.

## 4. Requisitos recomendados

### 4.1 Hardware

Configuración de referencia:

- CPU de 6 núcleos o superior;
- 32 GB de RAM recomendados;
- SSD de 1 TB para sistema y servicios;
- almacenamiento separado para fotografías y grabaciones;
- GPU compatible con el motor elegido, opcional;
- red Ethernet para servidor, cámaras y almacenamiento;
- NVMe externo para backup desconectable.

Una réplica sin GPU es viable usando modelos más pequeños y servicios CPU. El
stack completo simultáneo puede consumir bastante memoria; no debe levantarse
sin observar RAM, swap y disco.

### 4.2 Software base

- Ubuntu Server 24.04 LTS o distribución equivalente;
- Docker Engine y plugin Docker Compose;
- Git;
- `curl`, `jq`, `rsync`, `smartmontools` y `lm-sensors`;
- Python 3.11 o superior;
- Ollama;
- Tailscale, recomendado para acceso remoto;
- controlador GPU y ROCm solamente si el hardware lo soporta.

### 4.3 Puertos

Antes de desplegar:

```bash
sudo ss -lntup
```

Los puertos utilizados por la configuración de referencia aparecen en
`docs/inventario-servidor-odin.md`. Deben cambiarse si existe conflicto. No es
necesario exponerlos al router; basta con LAN y VPN.

## 5. Preparación del host

### 5.1 Crear usuario administrativo

```bash
sudo adduser odin
sudo usermod -aG sudo,docker odin
```

Cerrar sesión y volver a entrar para aplicar el grupo Docker. No se recomienda
ejecutar los contenedores desde la cuenta `root`.

### 5.2 Instalar dependencias

```bash
sudo apt update
sudo apt install -y \
  ca-certificates curl git jq rsync smartmontools lm-sensors \
  python3 python3-venv python3-pip sqlite3
```

Instalar Docker siguiendo el repositorio oficial de Docker para la distribución
elegida. Validar:

```bash
docker version
docker compose version
docker run --rm hello-world
```

### 5.3 Estructura de directorios

Adaptar el usuario y los discos:

```bash
sudo mkdir -p \
  /srv/odin/{core,audio,automation,media,monitoring,infra,scripts,data,logs,public} \
  /mnt/odin-data/{immich,frigate,backups}
sudo chown -R "$USER":"$USER" /srv/odin /mnt/odin-data
```

La instalación original utiliza `/home/k1k3/odin`; en una réplica se recomienda
`/srv/odin`. Los Compose del repositorio contienen rutas de referencia que deben
reemplazarse antes de desplegar:

```bash
rg '/home/k1k3|/mnt/almacen|/mnt/juegos' server-compose
```

No ejecutar `docker compose up` hasta haber revisado todas las rutas.

### 5.4 Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO> /srv/odin/repository
cd /srv/odin/repository
```

Crear una rama o copia privada para los ajustes del host. Nunca incorporar
`.env` reales al repositorio.

## 6. Gestión de secretos

### 6.1 Generar secretos

```bash
openssl rand -hex 32
openssl rand -base64 48
```

Cada servicio debe tener una contraseña distinta. Crear `.env` con permisos:

```bash
install -m 600 /dev/null .env
```

### 6.2 Plantilla del núcleo

Ejemplo orientativo para `server-compose/odin-master/.env`:

```dotenv
WEBUI_SECRET_KEY=GENERAR_UN_VALOR_ALEATORIO
NEXTCLOUD_DB_ROOT_PASSWORD=GENERAR_OTRO_VALOR
NEXTCLOUD_DB_PASSWORD=GENERAR_OTRO_VALOR
EVOLUTION_DB_PASSWORD=GENERAR_OTRO_VALOR
EVOLUTION_API_KEY=GENERAR_OTRO_VALOR
N8N_PUBLIC_URL=http://odin.local:5679/
CLOUDFLARED_TUNNEL_TOKEN=SOLO_SI_SE_UTILIZA_CLOUDFLARED
```

Si Cloudflared o Evolution API no forman parte de la réplica, eliminar sus
servicios del Compose en vez de inventar valores.

### 6.3 Comprobar que no se versionan secretos

```bash
git status --short
git check-ignore -v server-compose/odin-master/.env
```

Añadir patrones necesarios a `.gitignore`:

```gitignore
**/.env
**/.env.*
!**/.env.example
*.key
*.pem
```

## 7. Acceso remoto y nombres locales

### 7.1 Tailscale

Instalar Tailscale en servidor y clientes. Validar:

```bash
tailscale status
tailscale ip -4
```

No publicar Open WebUI, Qdrant, bases de datos o cámaras directamente en
Internet. Limitar el acceso a LAN, Tailscale o un proxy autenticado.

### 7.2 DNS y nombres

Opciones, de mejor a peor para una red doméstica:

1. DNS local en router, Pi-hole o AdGuard Home.
2. Tailscale MagicDNS.
3. Entradas `/etc/hosts` por dispositivo.

El script `tools/setup_odin_hostnames.sh` es un ejemplo para macOS, pero contiene
la IP de la instalación original. Copiarlo, cambiar IP y nombres, y ejecutarlo
solo en clientes controlados.

No existe un dominio multicast automático por escribir `odin.mealie`; debe
haber DNS, `/etc/hosts` o proxy que lo resuelva.

## 8. Ollama

### 8.1 Instalación

Instalar Ollama siguiendo su método oficial y habilitar:

```bash
sudo systemctl enable --now ollama
systemctl is-active ollama
curl http://127.0.0.1:11434/api/version
```

### 8.2 Modelo conversacional y embeddings

La instalación de referencia usa:

```bash
ollama pull ministral-3:14b
ollama pull mxbai-embed-large
```

En máquinas con menos RAM:

```bash
ollama pull qwen3:8b
```

La selección debe comprobar capacidad de tools, idioma, visión y memoria
disponible. No asumir que un modelo de texto interpreta fotos.

### 8.3 Contexto

Odín usa 16384 tokens en Open WebUI. Empezar con 8192 si hay presión de memoria.
Comprobar el modelo cargado:

```bash
curl -s http://127.0.0.1:11434/api/ps | jq
```

Buscar `context_length`. Los prompts largos pueden truncarse sin que Ollama esté
averiado.

### 8.4 GPU

Con AMD/ROCm:

```bash
rocminfo
rocm-smi
journalctl -u ollama --since "1 hour ago"
```

No copiar variables como `HSA_OVERRIDE_GFX_VERSION` sin confirmar la
arquitectura de la GPU. Una configuración incorrecta puede provocar fallos del
runner.

## 9. Núcleo: Open WebUI, Qdrant, Nextcloud y n8n

### 9.1 Preparar el Compose

Copiar:

```bash
mkdir -p /srv/odin/core/odin-master
cp server-compose/odin-master/docker-compose.yml /srv/odin/core/odin-master/
cd /srv/odin/core/odin-master
```

Editar rutas persistentes y crear:

```bash
mkdir -p data/{openweb_ui_data,qdrant,nextcloud,nextcloud_db,n8n,evolution_db}
```

El Compose saneado monta Open WebUI desde una ruta absoluta. Cambiarla por:

```yaml
- /srv/odin/data/openweb_ui_data:/app/backend/data
```

### 9.2 Despliegue gradual

No levantar todo de golpe:

```bash
docker compose config
docker compose up -d qdrant-odin db-nextcloud nextcloud-odin
docker compose ps
docker compose logs --tail=100 qdrant-odin nextcloud-odin
```

Después:

```bash
docker compose up -d webui-odin n8n-odin crawl4ai stirling-pdf
```

Evolution API y Cloudflared son opcionales.

### 9.3 Inicializar Nextcloud

Abrir `http://IP_SERVIDOR:8082`, crear el administrador y confirmar:

```bash
curl -I http://127.0.0.1:8082/
```

Configurar dominios de confianza y proxy según la documentación de Nextcloud.

### 9.4 Inicializar Open WebUI

Abrir `http://IP_SERVIDOR:3000`, crear la cuenta administradora y desactivar
registro público después:

```yaml
ENABLE_SIGNUP=False
```

Comprobar conexión a Ollama y Qdrant. Crear el modelo personalizado `odn` u otro
nombre y configurar inicialmente:

```json
{
  "num_ctx": 16384
}
```

### 9.5 Validación

```bash
curl -f http://127.0.0.1:3000/health
curl -f http://127.0.0.1:6333/collections
curl -I http://127.0.0.1:5679/
```

## 10. Immich

### 10.1 Preparar datos

```bash
mkdir -p /srv/odin/media/immich
mkdir -p /mnt/odin-data/immich/{library,postgres}
cp server-compose/immich/docker-compose.yml /srv/odin/media/immich/
```

El Compose referencia `hwaccel.ml.yml`, que debe obtenerse de la versión de
Immich correspondiente o eliminarse si no se usa ROCm.

### 10.2 `.env`

```dotenv
UPLOAD_LOCATION=/mnt/odin-data/immich/library
DB_DATA_LOCATION=/mnt/odin-data/immich/postgres
IMMICH_VERSION=release
DB_PASSWORD=GENERAR_CONTRASEÑA
DB_USERNAME=postgres
DB_DATABASE_NAME=immich
```

### 10.3 Elegir aceleración

- CPU: usar la imagen estándar de machine learning.
- NVIDIA: usar el perfil oficial CUDA compatible.
- AMD: usar ROCm solo si está soportado y `/dev/kfd` funciona.

No conservar `HSA_OVERRIDE_GFX_VERSION=12.0.0` sin validación.

### 10.4 Arranque y prueba

```bash
cd /srv/odin/media/immich
docker compose config
docker compose up -d
docker compose ps
curl -f http://127.0.0.1:2283/api/server/ping
```

Crear usuario, generar una API key dedicada para la tool y limitar su custodia.

## 11. Mealie

### 11.1 Compose

Crear `/srv/odin/media/mealie/docker-compose.yml`:

```yaml
services:
  mealie:
    image: ghcr.io/mealie-recipes/mealie:v1.12.0
    container_name: mealie
    ports:
      - "9925:9000"
    volumes:
      - ./data:/app/data
    environment:
      ALLOW_SIGNUP: "false"
      PUID: "1000"
      PGID: "1000"
      TZ: Europe/Madrid
      BASE_URL: http://IP_SERVIDOR:9925
    restart: unless-stopped
```

Durante la creación del primer usuario puede habilitarse temporalmente
`ALLOW_SIGNUP=true`. Desactivarlo después.

```bash
docker compose up -d
curl -I http://127.0.0.1:9925
```

Crear un token de larga duración dedicado a Open WebUI. No usar la contraseña
del usuario dentro de la tool.

## 12. Frigate

### 12.1 Preparación

```bash
mkdir -p /srv/odin/automation/frigate/config
mkdir -p /mnt/odin-data/frigate
cp server-compose/frigate/docker-compose.yml /srv/odin/automation/frigate/
```

Cambiar el volumen de grabaciones a `/mnt/odin-data/frigate`.

### 12.2 Configuración mínima

Crear `config/config.yml` usando secretos o variables para RTSP:

```yaml
mqtt:
  enabled: false

detectors:
  cpu1:
    type: cpu

cameras:
  entrada:
    ffmpeg:
      inputs:
        - path: rtsp://USUARIO:CONTRASEÑA@IP_CAMARA/STREAM
          roles:
            - detect
            - record
    detect:
      width: 1280
      height: 720
      fps: 5
    objects:
      track:
        - person
```

La URL exacta depende del fabricante. Probarla primero con `ffprobe` o VLC. No
publicar RTSP fuera de LAN/VPN.

### 12.3 Arranque

```bash
cd /srv/odin/automation/frigate
docker compose config
docker compose up -d
docker compose logs -f frigate
```

Validar:

```bash
curl -s http://127.0.0.1:5001/api/stats | jq '.cameras'
curl -o /tmp/camera.jpg \
  http://127.0.0.1:5001/api/entrada/latest.jpg
file /tmp/camera.jpg
```

### 12.4 Reconocimiento de personas

`ultima_persona` aprovecha `sub_label` si Frigate ha reconocido una cara. La
configuración de reconocimiento depende de la versión de Frigate y requiere
imágenes de referencia. Verificar primero que los eventos tienen:

```json
{
  "label": "person",
  "has_snapshot": true,
  "sub_label": "NOMBRE"
}
```

## 13. Home Assistant

### 13.1 Instalación separada

La arquitectura recomendada mantiene Home Assistant OS en Raspberry Pi o
máquina dedicada. Esto conserva la domótica aunque el servidor de IA se
reinicie.

### 13.2 Proxy opcional

Copiar:

```bash
mkdir -p /srv/odin/automation/home-assistant-proxy
cp server-compose/home-assistant-proxy/docker-compose.yml \
  /srv/odin/automation/home-assistant-proxy/
```

Crear `.env`:

```dotenv
HOME_ASSISTANT_HOST=IP_REAL_DE_HOME_ASSISTANT
```

Arrancar:

```bash
docker compose --env-file .env up -d
curl -I http://127.0.0.1:8123/api/
```

Un `401 Unauthorized` sin token confirma que la API responde.

### 13.3 Token

En Home Assistant:

1. abrir el perfil del usuario;
2. crear un token de acceso de larga duración;
3. guardarlo en valves o `.env` de la integración;
4. no incluirlo en el código exportado.

Validar:

```bash
curl -H "Authorization: Bearer $HA_TOKEN" \
  http://127.0.0.1:8123/api/
```

### 13.4 Entidades

La tool no puede controlar nombres inexistentes. Enumerar:

```bash
curl -s -H "Authorization: Bearer $HA_TOKEN" \
  http://127.0.0.1:8123/api/states |
  jq -r '.[] | [.entity_id, .attributes.friendly_name, .state] | @tsv'
```

Adaptar en la tool:

- entidad del aspirador;
- calendario;
- lista de compra;
- alias locales;
- nombres de cámaras o áreas.

### 13.5 STT y TTS mediante Wyoming

Copiar el Compose de `server-compose/audio/`, corregir rutas y arrancar:

```bash
docker compose up -d wyoming-whisper piper
```

En Home Assistant añadir integraciones Wyoming:

- Whisper: `IP_SERVIDOR`, puerto `10300`;
- Piper: `IP_SERVIDOR`, puerto `10200`.

Crear o editar el pipeline Assist y seleccionar:

- STT: `faster-whisper` o Wyoming Whisper;
- idioma: español;
- TTS: Piper.

Si uno no aparece, comprobar contenedor, puerto, firewall y logs antes de
recrear el pipeline.

## 14. Servicios de voz adicionales

El Compose de audio incluye alternativas:

- `faster-whisper-server`, puerto 10301;
- `wyoming-whisper`, puerto 10300;
- Piper, puerto 10200;
- `odin-asr`, que requiere construir una imagen y aportar modelos;
- PocketTTS, experimental.

Para una réplica inicial desplegar solo Wyoming Whisper y Piper. Añadir el resto
después de medir RAM y latencia.

## 15. Monitorización

### 15.1 Netdata

```bash
mkdir -p /srv/odin/monitoring/netdata
cp server-compose/netdata/docker-compose.yml /srv/odin/monitoring/netdata/
cd /srv/odin/monitoring/netdata
mkdir -p config lib cache
docker compose up -d
curl -f http://127.0.0.1:19999/api/v1/info
```

El contenedor tiene permisos elevados de observación. Mantenerlo limitado a
LAN/VPN.

### 15.2 Exportador para Home Assistant

Copiar:

```bash
install -m 755 tools/odin_ha_status.py /srv/odin/scripts/
mkdir -p /srv/odin/public /srv/odin/logs/health
```

Adaptar las constantes de rutas y endpoints. Instalar la unidad:

```bash
sudo cp server-systemd/odin-health-http.service \
  /etc/systemd/system/odin-health-http.service
sudo systemctl daemon-reload
sudo systemctl enable --now odin-health-http
```

Validar:

```bash
/srv/odin/scripts/odin_ha_status.py
curl http://127.0.0.1:8765/ha_status.json | jq
```

### 15.3 Autoreparación conservadora

```bash
install -m 755 tools/odin_autorepair.py /srv/odin/scripts/
/srv/odin/scripts/odin_autorepair.py
```

Revisar todas las rutas constantes antes de programarlo. El modo reparación no
debe tener sudo ilimitado. Si se permite arrancar Ollama sin contraseña, crear
una regla `sudoers` limitada exclusivamente a esa unidad y validarla con
`visudo`.

## 16. Ingesta documental y Qdrant

La réplica completa requiere un script de ingesta que:

1. recorra una carpeta de Nextcloud;
2. extraiga texto de formatos permitidos;
3. divida documentos en fragmentos;
4. genere embeddings con un único modelo;
5. escriba vectores y metadatos en Qdrant;
6. conserve una caché de cambios.

No mezclar modelos con dimensiones distintas dentro de la misma colección.
Para `mxbai-embed-large`, crear la colección con la dimensión que devuelva el
modelo utilizado por la implementación.

El wrapper `tools/cron_odin_ingesta.sh` presupone:

```text
/srv/odin/scripts/odin_ingesta_master.py
```

Ese script principal debe aportarse o implementarse antes de activar cron.
Probar manualmente y comprobar la colección:

```bash
curl -s http://127.0.0.1:6333/collections/NOMBRE_COLECCION | jq
```

Solo después:

```cron
0 * * * * /srv/odin/scripts/cron_odin_ingesta.sh >> /srv/odin/logs/ingesta.log 2>&1
```

## 17. Proxies especializados

Los proxies solucionan dos problemas:

- las tools no deben contener tokens;
- el navegador del cliente no puede cargar `127.0.0.1` del servidor.

Puertos de referencia:

| Puerto | Proxy |
| ---: | --- |
| 2290 | imágenes de Immich |
| 2291 | notas de Nextcloud |
| 2292 | operaciones de Mealie |
| 2293 | imágenes de Frigate |

Cada proxy debe:

- escuchar solo en LAN/VPN o firewall;
- aceptar únicamente operaciones conocidas;
- validar identificadores y URLs;
- aplicar timeouts;
- no devolver secretos;
- usar CORS solamente para contenido visual necesario;
- registrar errores sin incluir tokens.

No construir un proxy genérico que permita al modelo solicitar cualquier URL.

## 18. Importar las tools de Open WebUI

### 18.1 Orden recomendado

1. QR, para validar que Open WebUI carga tools.
2. Salud del sistema en modo consulta.
3. Nextcloud e Immich.
4. YouTube/Crawl4AI.
5. Mealie.
6. Frigate.
7. Home Assistant y acciones físicas al final.

### 18.2 Artefactos

`tools/openwebui-tools/` contiene exports saneados y el catálogo
`index.json`. Antes de importar:

```bash
rg -n 'TOKEN|API_KEY|192\\.168|127\\.0\\.0\\.1|piquique|webhook' \
  tools/openwebui-tools
```

Sustituir placeholders mediante valves o variables. No importar un export
histórico sin compararlo con `index.json` y
`docs/estado-final-tools-integraciones-2026-06-09.md`.

### 18.3 Prompt del modelo

El prompt debe ser corto y determinista:

- usar la tool específica para cada dominio;
- no decir “ejecutando” antes de llamar;
- no afirmar una acción sin resultado de la tool;
- copiar literalmente Markdown de imágenes;
- devolver errores reales;
- usar funciones atómicas para acciones críticas.

Evitar repetir la misma regla en muchos párrafos, porque aumenta el contexto y
puede introducir contradicciones.

### 18.4 Acciones atómicas

Para dispositivos físicos, preferir:

```text
controlar_aspirador("iniciar")
```

frente a:

```text
buscar_entidad("aspirador")
execute_action(resultado, "start")
```

La primera forma reduce llamadas, ambigüedad y confirmaciones falsas. Adaptar el
ID de entidad a la réplica.

### 18.5 Imágenes Markdown

La salida debe tener exactamente:

```markdown
![Descripción](http://SERVIDOR:PUERTO/recurso)
```

La URL debe ser accesible desde el navegador del cliente. Una URL
`http://127.0.0.1:...` apuntaría al cliente, no al servidor.

## 19. Pruebas de aceptación

### 19.1 Infraestructura

```bash
docker compose ls
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
systemctl is-active ollama
```

### 19.2 Endpoints

```bash
curl -f http://127.0.0.1:3000/health
curl -f http://127.0.0.1:11434/api/version
curl -f http://127.0.0.1:6333/collections
curl -f http://127.0.0.1:2283/api/server/ping
curl -I http://127.0.0.1:9925
curl -s http://127.0.0.1:5001/api/stats | jq
curl -f http://127.0.0.1:19999/api/v1/info
```

### 19.3 Tools

Probar en conversaciones nuevas:

1. “Transcribe este vídeo de YouTube: URL”.
2. “Busca una foto de DESCRIPCIÓN”.
3. “Guarda esta nota en Nextcloud”.
4. “Crea una receta de prueba en Mealie”.
5. “Enséñame la cámara”.
6. “¿Quién fue la última persona detectada?”.
7. “Dime el estado del aspirador sin arrancarlo”.
8. Con autorización física: “Inicia el aspirador”.

Comprobar en Open WebUI que aparece la fuente de la función correcta. No aceptar
como prueba una respuesta que solo diga que está procesando.

### 19.4 Restauración

Una réplica no está terminada hasta restaurar:

- una nota de Nextcloud;
- una receta de Mealie;
- una configuración de tool;
- una foto o metadato de Immich;
- una colección o snapshot de Qdrant.

## 20. Backup

### 20.1 Datos críticos

Respaldar:

- Compose, `.env` cifrados y documentación;
- datos de Open WebUI;
- Nextcloud y su MariaDB;
- n8n;
- Qdrant o snapshots de colecciones;
- Mealie;
- configuración de Frigate;
- PostgreSQL y biblioteca de Immich;
- scripts, cron y unidades systemd.

No copiar bases de datos activas de forma inconsistente. Usar dumps o detener
el stack correspondiente.

### 20.2 NVMe externo

Identificar:

```bash
lsblk -o NAME,MODEL,SERIAL,SIZE,FSTYPE,UUID,MOUNTPOINTS
sudo smartctl -a /dev/UNIDAD
```

Usar UUID en `/etc/fstab`, preferiblemente con `noauto,nofail`. Considerar LUKS
si contiene datos personales. Ejecutar copias con log y desmontar:

```bash
sync
sudo umount /mnt/odin-backup
```

Mantener la unidad desconectada protege frente a borrados accidentales,
ransomware y errores del host.

## 21. Medición de consumo

Integrar enchufes con medición en Home Assistant. Deben exponer:

- potencia instantánea en W;
- energía acumulada en kWh;
- disponibilidad;
- idealmente tensión y corriente.

Registrar al menos:

1. servidor en reposo;
2. modelo descargado de memoria;
3. modelo cargado;
4. generación LLM;
5. procesamiento de fotos;
6. carga simultánea.

Calcular:

```text
coste = energía_kWh * precio_EUR_por_kWh
```

No estimar el consumo desde el TDP del hardware cuando ya se dispone de
medición física.

## 22. Actualizaciones

Antes de actualizar:

```bash
docker compose config > compose.resolved.before.yml
docker compose images
docker compose ps
```

Respaldar bases y revisar notas de versión. Evitar `latest` en servicios
críticos cuando se necesite reproducibilidad. Actualizar un stack por vez:

```bash
docker compose pull
docker compose up -d
docker compose logs --tail=200
```

No ejecutar simultáneamente actualizaciones de Nextcloud, Immich, Open WebUI y
bases de datos.

## 23. Diagnóstico

### Open WebUI no conecta con Ollama

```bash
curl http://127.0.0.1:11434/api/version
docker exec webui-odin curl http://127.0.0.1:11434/api/version
journalctl -u ollama -n 200 --no-pager
```

Con `network_mode: host`, Open WebUI puede usar `127.0.0.1`. En una red bridge,
debe usar nombre de servicio o `host.docker.internal`.

### El modelo promete una acción pero no la ejecuta

- comprobar que la tool está asignada al modelo;
- revisar el esquema de parámetros;
- eliminar tools duplicadas;
- usar una función atómica;
- prohibir mensajes previos de “procesando”;
- probar en un chat nuevo.

### La imagen aparece como enlace o no carga

- conservar `![texto](url)`;
- probar la URL desde otro dispositivo;
- comprobar CORS y `Content-Type`;
- evitar `127.0.0.1`;
- añadir un parámetro de tiempo para evitar caché;
- revisar contenido mixto HTTP/HTTPS.

### Home Assistant no encuentra un dispositivo

- listar entidades reales;
- buscar por dominio;
- añadir alias;
- comprobar que no está `unavailable`;
- llamar al servicio manualmente con la API antes de culpar al modelo.

### Frigate no muestra eventos

```bash
curl 'http://127.0.0.1:5001/api/events?camera=entrada&limit=5'
docker logs --tail=200 frigate
```

Confirmar `has_snapshot`, etiqueta `person`, nombre de cámara y retención.

### Ollama parece bloqueado después de un vídeo

Buscar:

```bash
journalctl -u ollama --since "30 minutes ago" | grep -i truncat
curl http://127.0.0.1:11434/api/ps | jq
```

El problema puede ser contexto agotado, no un servicio caído. Abrir una
conversación nueva y ajustar `num_ctx` con prudencia.

## 24. Endurecimiento de seguridad

- desactivar registro público de Open WebUI y Mealie;
- usar MFA donde esté disponible;
- restringir puertos mediante firewall;
- no publicar bases de datos;
- usar usuarios y tokens dedicados;
- rotar credenciales expuestas;
- mantener logs sin secretos;
- cifrar backups;
- separar red de cámaras/IoT cuando sea posible;
- revisar permisos de Docker, porque pertenecer al grupo `docker` equivale
  prácticamente a privilegios de root;
- conservar un inventario de puertos y dependencias.

Ejemplo UFW, adaptando la subred:

```bash
sudo ufw default deny incoming
sudo ufw allow OpenSSH
sudo ufw allow from 192.168.1.0/24 to any port 3000 proto tcp
sudo ufw allow in on tailscale0
sudo ufw enable
```

No copiar estas reglas sin mantener acceso SSH alternativo.

## 25. Orden completo de despliegue

Checklist recomendada:

- [ ] Preparar usuario, Docker, almacenamiento y VPN.
- [ ] Generar secretos y revisar rutas.
- [ ] Instalar Ollama y un modelo pequeño.
- [ ] Desplegar Qdrant y Open WebUI.
- [ ] Validar chat local.
- [ ] Desplegar Nextcloud y n8n.
- [ ] Desplegar Netdata y exportador de salud.
- [ ] Desplegar Immich.
- [ ] Desplegar Mealie.
- [ ] Conectar Home Assistant y validar token.
- [ ] Desplegar Wyoming Whisper y Piper.
- [ ] Configurar Frigate con una cámara.
- [ ] Crear proxies especializados.
- [ ] Importar tools de solo lectura.
- [ ] Importar tools de escritura.
- [ ] Añadir acciones físicas atómicas.
- [ ] Ejecutar pruebas de aceptación.
- [ ] Configurar ingesta y cron.
- [ ] Configurar backup y restaurarlo.
- [ ] Integrar medición eléctrica.
- [ ] Documentar cambios propios.

## 26. Criterio de réplica completada

La réplica se considera funcional cuando:

- Open WebUI conversa con un modelo local;
- la memoria vectorial responde;
- Nextcloud guarda y recupera una nota;
- Immich devuelve una foto;
- Mealie crea una receta;
- Frigate devuelve una captura;
- Home Assistant ejecuta una acción autorizada;
- STT y TTS funcionan en un pipeline;
- Netdata y el JSON de salud responden;
- las tools muestran fuentes reales;
- existe un backup restaurado con éxito;
- no hay secretos dentro del repositorio.

Una instalación que solo levanta contenedores no replica Odín. La aportación del
proyecto está en integrar servicios, tools, evidencias, seguridad y operación
reproducible.
