# Estado final de tools e integraciones de Odín

Fecha de consolidación: 2026-06-09

Este documento recoge el estado operativo alcanzado durante la recuperación del
servidor tras el cambio de red doméstica. No contiene tokens, claves API,
contraseñas ni identificadores secretos.

## Cambio de red y criterio de conectividad

El servidor Odín utiliza actualmente la dirección LAN `192.168.1.133`. Varias
integraciones conservaban direcciones de la red anterior `192.168.86.0/24`, por
lo que fallaban aunque sus servicios siguieran funcionando.

La corrección no se limitó a sustituir direcciones. Las integraciones que se
ejecutan en el propio servidor usan `127.0.0.1` para evitar depender de la IP
LAN. Cuando una imagen debe cargarla el navegador de otro dispositivo, se
publica una URL LAN mediante un proxy específico. Los secretos se mantienen en
`.env`, valves de Open WebUI o ficheros con permisos restringidos.

## Modelo conversacional

Odín se ejecuta en Open WebUI sobre `ministral-3:14b` servido por Ollama.

- Ollama se ejecuta como servicio `systemd` en el host.
- El modelo admite hasta 262144 tokens según sus metadatos.
- Open WebUI estaba cargándolo con 4096 tokens y una transcripción de YouTube
  produjo truncado al alcanzar 4265 tokens.
- El parámetro de Odín quedó fijado en `num_ctx=16384`.
- Se verificó en `/api/ps` que Ollama cargaba el modelo con
  `context_length=16384`.
- El modelo ocupa aproximadamente 12,7 GB al cargarse con este contexto.

El aumento reduce los truncados, aunque sigue siendo recomendable iniciar una
conversación nueva después de procesar vídeos o documentos excepcionalmente
largos.

## Tools activas asignadas al modelo Odín

El modelo tiene asignadas nueve tools principales:

| ID | Funciones | Estado y finalidad |
| --- | --- | --- |
| `guardar_transcripcion_de_video_o_pagina_web` | `get_youtube_transcript`, `search_and_crawl_web` | Extrae subtítulos reales de YouTube y contenido web. La primera acción ante una petición de vídeo debe ser la llamada a la tool; se prohíben mensajes ficticios de espera. |
| `guardar_nota` | `guardar_nota_nextcloud` | Guarda notas Markdown en Nextcloud mediante el proxy local y n8n. |
| `home_assistant` | `controlar_aspirador`, `control_home_assistant`, `get_health_status`, `manage_calendar`, `manage_shopping_list` | Control domótico estructurado. La acción del aspirador es atómica y no depende de una segunda llamada del modelo. |
| `qr_code_generator_for_open_webui` | `generate_qr_code` | Genera códigos QR en el chat. |
| `buscar_fotos` | `buscar_foto` | Busca recuerdos en Immich y devuelve Markdown de imagen renderizable. |
| `buscar_nextcloud` | `buscar_en_nextcloud` | Consulta notas y documentos personales indexados. |
| `salud_del_sistema` | `manage_system_health` | Consulta el estado operativo del servidor mediante la integración local. |
| `vigilancia_frigate` | `ultima_persona`, `consultar_camaras`, `ver_foto_actual`, `ver_ultimo_evento` | Consulta Frigate y devuelve capturas mediante un proxy de imágenes. |
| `mealie_recetas` | `crear_receta`, `importar_receta_url`, `importar_receta_imagen` | Crea e importa recetas en Mealie desde texto, URL o imagen. |

Las tools históricas `lista_de_la_compra` y `recordatorio` siguen registradas en
Open WebUI, pero no se asignan al modelo porque sus funciones ya están
consolidadas en `home_assistant`. El conector duplicado
`home_assistant_connector` fue eliminado.

## Home Assistant

Home Assistant se ejecuta en una Raspberry Pi independiente. El servidor accede
a él por el puerto local `8123`. La tool principal se corrigió para usar
`http://127.0.0.1:8123` en lugar de la IP antigua.

La API y el token se validaron consultando configuración y 577 entidades. Se
confirmó la existencia de:

- calendario `calendar.mycal`;
- lista `todo.lista_de_la_compra`;
- aspirador `vacuum.d10_plus_gen_2`;
- sensores, interruptores y entidades auxiliares del Dreame D10 Plus Gen 2.

### Búsqueda estructurada

La búsqueda inicial usaba únicamente similitud textual. La palabra
`aspirador` no se parecía a `D10 Plus Gen 2` y devolvía entidades absurdas. La
búsqueda actual añade alias y dominio:

- aspirador, robot, Dreame, D10 y Roomba se asocian a `vacuum`;
- luces y lámparas se asocian a `light`;
- enchufes e interruptores se asocian a `switch`;
- persianas y cortinas se asocian a `cover`;
- clima y termostato se asocian a `climate`.

### Acción atómica del aspirador

El patrón buscar entidad y después ejecutar servicio dependía de que el modelo
hiciera dos llamadas. En ocasiones Odín encontraba el aspirador, escribía
“ejecutando” y nunca llamaba a la acción real.

Se añadió `controlar_aspirador(accion)`, que actúa en una sola llamada sobre
`vacuum.d10_plus_gen_2`:

| Acción natural | Servicio Home Assistant |
| --- | --- |
| iniciar o limpiar | `vacuum.start` |
| pausar | `vacuum.pause` |
| detener o parar | `vacuum.stop` |
| volver o base | `vacuum.return_to_base` |

La función espera brevemente, consulta de nuevo el estado y solo entonces
devuelve confirmación o el error real. Las funciones ambiguas
`ask_home_assistant` y `execute_action` se retiraron del esquema visible para
órdenes del aspirador.

## Frigate

Frigate está publicado internamente en `5001` y detecta la cámara
`tapo_salon`. La detección se ejecuta en CPU. La tool usa
`127.0.0.1:5001/api` para consultar cámaras y eventos.

El navegador no siempre podía renderizar las imágenes servidas directamente
desde la API privada. Se creó `frigate-image-proxy`, puerto `2293`, que:

- solo permite capturas actuales y snapshots de eventos;
- devuelve `Content-Type: image/jpeg`;
- añade `Access-Control-Allow-Origin: *`;
- desactiva caché;
- valida cámara e identificador de evento.

Las funciones visuales devuelven una línea Markdown que el modelo debe copiar
sin modificar. Si solo existe una cámara, se selecciona automáticamente.

La función `ultima_persona` filtra eventos `person`, exige snapshot y utiliza
`sub_label` cuando Frigate reconoce a alguien. En la prueba final recuperó a
`QUIQUE` y devolvió su imagen. Para Odín, `tapo_salon` representa la cámara de
la entrada aunque el identificador técnico conserve el nombre original.

## Immich

La tool `buscar_fotos` consulta la búsqueda inteligente de Immich y devuelve
una imagen Markdown. El navegador obtiene la imagen a través de
`immich-photo-proxy`, puerto `2290`, evitando depender del webhook público que
había quedado asociado a la red anterior.

## Nextcloud

El guardado de notas se corrigió mediante `nextcloud-note-proxy`, puerto `2291`.
El proxy encapsula la conexión con n8n y evita que la tool dependa directamente
de una URL pública susceptible a cambios de red. Se verificó el guardado real,
no únicamente la generación de una confirmación conversacional.

## Mealie

Mealie se desplegó con la imagen `ghcr.io/mealie-recipes/mealie:v1.12.0` y se
publica en el puerto LAN `9925`. Sus datos persistentes se encuentran bajo
`/home/k1k3/odin/media/mealie/data`.

Se generó un token de larga duración dedicado a Open WebUI, almacenado fuera
del código. `mealie-tool-proxy`, puerto `2292`, ofrece tres operaciones:

- crear receta desde nombre, ingredientes, pasos, tiempos y raciones;
- importar una receta desde una URL compatible con el scraper de Mealie;
- importar desde imagen o descargar una imagen pública y asociarla a la receta.

La creación desde texto y la carga de imagen se verificaron de extremo a
extremo. Las recetas de prueba se eliminaron. La interpretación de una foto
adjunta depende de que el modelo seleccionado disponga de visión.

## YouTube y Crawl4AI

La librería `youtube-transcript-api` se probó dentro del contenedor de Open
WebUI y obtuvo una transcripción real. El problema observado no era de red ni
de librería: el modelo narraba “procesando” sin ejecutar la función.

La descripción y el prompt obligan ahora a llamar primero a
`get_youtube_transcript`. Se prohíben mensajes de espera simulada. Si la
extracción falla, se devuelve el error real. La prueba de extremo a extremo
mostró la fuente de la tool y el texto transcrito.

## Salud del sistema

La tool `salud_del_sistema` quedó conectada a la ruta actual de automatización.
Su objetivo es consultar Docker, Ollama, disco, GPU, memoria y servicios sin
inventar resultados. Se complementa con Netdata, el exportador JSON para Home
Assistant y `odin_autorepair.py`.

## Proxies locales añadidos

| Contenedor | Puerto | Finalidad |
| --- | ---: | --- |
| `immich-photo-proxy` | 2290 | Servir fotos de Immich al navegador. |
| `nextcloud-note-proxy` | 2291 | Guardar notas mediante n8n/Nextcloud. |
| `mealie-tool-proxy` | 2292 | Crear e importar recetas sin exponer el token. |
| `frigate-image-proxy` | 2293 | Servir capturas y snapshots JPEG con CORS. |
| `odin-local-proxy` | según Caddy | Resolver nombres y accesos locales del ecosistema. |

## Servicios recuperados o incorporados

Además de las tools, durante la recuperación quedaron operativos Open WebUI,
Ollama, n8n, Nextcloud, Qdrant, Immich, Frigate, Mealie, Netdata, Crawl4AI,
Stirling PDF, Evolution API, Piper, faster-whisper, Wyoming Whisper, Odin ASR y
PocketTTS.

## Estado de cierre

La medición de consumo está integrada mediante dos enchufes Sonoff y aparece
en Home Assistant. El NVMe externo está identificado por UUID, montado en
`/mnt/backup_nvme` y contiene un repositorio Restic cifrado. El backup cubre
infraestructura, Nextcloud e Immich, aplica retención y se programa a las
04:00 tras validar integridad y restauración.

### Checklist de consumo

- [x] Conectar los dos enchufes inteligentes.
- [x] Integrarlos en Home Assistant.
- [x] Confirmar entidades de potencia instantánea y energía acumulada.
- [x] Asignar nombres y áreas estables.
- [x] Crear histórico y panel de energía.
- [x] Medir el régimen habitual y observar picos de inferencia.
- [x] Calcular una estimación mensual.
- [x] Incorporar las gráficas y resultados a la memoria.

### Checklist de backup NVMe

- [x] Conectar el NVMe y registrar modelo y capacidad.
- [x] Identificar la unidad por UUID para no depender de `/dev/sdX`.
- [x] Decidir cifrado, sistema de ficheros y punto de montaje.
- [x] Definir la copia de infraestructura y sus exclusiones regenerables.
- [x] Incluir configuraciones, bases de datos, fotos, Nextcloud y tools.
- [x] Volcar correctamente MariaDB antes de copiar.
- [x] Ejecutar una copia local con código de salida verificable.
- [x] Generar comprobaciones de integridad SHA-256.
- [x] Configurar montaje persistente con `nofail` y permisos restrictivos.
- [x] Restaurar una muestra y comparar su SHA-256.
