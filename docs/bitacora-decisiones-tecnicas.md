# Bitácora de decisiones técnicas de Odín

Fecha de inicio: 2026-05-07

Este documento recoge decisiones, problemas y rutas descartadas. Su objetivo es servir como materia prima para la memoria, especialmente para los capítulos de diseño, desarrollo, riesgos y trabajo futuro.

## Regla de trabajo

El servidor contiene pruebas, servicios activos, servicios abandonados y configuraciones con estado. No se debe mover, borrar ni reordenar nada sin una copia y una decisión explícita. Primero se documenta; luego se planifica; por último se cambia.

## Acceso remoto

### Decisión actual

El acceso remoto se realiza mediante Tailscale/VPN, no mediante WireGuard manual.

### Motivo

La solución anterior con DuckDNS era inestable en determinados momentos de alta demanda de red, especialmente cuando había fútbol y DuckDNS fallaba o se volvía poco fiable. Tailscale simplifica el acceso remoto al servidor sin exponer puertos directamente a Internet y reduce la dependencia de DNS dinámico.

### Cómo explicarlo en la memoria

Tailscale se puede presentar como la evolución práctica del requisito de acceso remoto seguro. La planificación inicial hablaba de túneles tipo WireGuard; la implementación final adopta Tailscale como capa VPN basada en WireGuard, elegida por estabilidad operativa y menor carga de mantenimiento.

## Home Assistant como habitación inteligente

Home Assistant concentra la automatización de la habitación inteligente. El sistema puede controlarse tanto desde la interfaz propia de Home Assistant como desde Open WebUI, que actúa como interfaz conversacional principal de Odín.

Punto clave para la memoria: Odín no sustituye a Home Assistant. Lo convierte en una capacidad conversacional y orquestable desde el asistente.

## Open WebUI como interfaz principal

Open WebUI no se utiliza solo como chat para un LLM. Es el centro de interacción desde el que se controlan la mayoría de acciones mediante tools.

Tools detectadas en la base de datos de Open WebUI:

| ID | Nombre | Función |
| --- | --- | --- |
| `buscar_fotos` | buscar fotos | Buscar fotos en Immich |
| `guardar_nota` | Guardar nota en Nextcloud | Guardar notas, resúmenes y documentos en Nextcloud vía n8n |
| `recordatorio` | Recordatorio | Crear recordatorios en calendario de Home Assistant |
| `lista_de_la_compra` | Lista de la compra | Añadir productos a la lista de compra de Home Assistant |
| `buscar_nextcloud` | Buscar Nextcloud | Buscar en notas de Nextcloud |
| `salud_del_sistema` | salud del sistema | Consultar salud del sistema |
| `vigilancia_frigate` | vigilancia_frigate | Consultas/acciones relacionadas con Frigate |
| `qr_code_generator_for_open_webui` | QR Code Generator for Open WebUI | Generar QR dentro del chat |
| `home_assistant` | Home Assistant | Control de domótica, calendario, compra y salud desde Home Assistant |
| `guardar_transcripcion_de_video_o_pagina_web` | Guardar transcripción de video o página web | Lectura web/YouTube con Crawl4AI y transcripciones |
| `home_assistant_connector` | Home assistant connector | Puente directo con Home Assistant Assist |

Estas tools son una de las diferencias más importantes de Odín frente a un chatbot genérico: convierten el lenguaje natural en acciones sobre servicios locales.

## Voz y TTS

La voz es uno de los mayores bloqueos técnicos del proyecto.

### Objetivo

Conseguir una voz realista y rápida para Odín, compatible con el ecosistema local y suficientemente fluida para interacción cotidiana.

### Problema principal

La GPU AMD complica mucho el despliegue de TTS moderno acelerado. Muchas herramientas están más maduras para NVIDIA/CUDA que para AMD/ROCm. Esto ha provocado pruebas fallidas, latencias altas o incompatibilidades.

### Herramientas probadas o usadas

| Herramienta | Estado | Observación |
| --- | --- | --- |
| Piper | En uso | Se usa para el asistente físico/móvil. Voz menos realista, pero estable y rápida. |
| PocketTTS | En uso/prueba actual | Probado después de otras alternativas como servidor TTS compatible con estilo OpenAI. |
| Kokoro | Probado | Prueba previa, no consolidada como solución final. |
| Chatterbox | Probado | Único que llegó a funcionar en GPU, pero iba demasiado lento para el caso de uso. |
| Otros TTS | Probados | Quedan como rutas descartadas o experimentos en cuarentena. |

### Cómo explicarlo en la memoria

El TTS debe tener una subsección propia dentro de desarrollo/problemas encontrados. Es un ejemplo claro de ingeniería real: el mejor modelo teórico no sirve si la latencia, la compatibilidad o el consumo rompen la experiencia.

## Frigate

Frigate se utiliza para vigilancia y detección de personas.

### Decisión actual

La detección se ejecuta en CPU, no en GPU.

### Motivo

Funciona lo suficientemente bien en CPU y evita saturar la GPU AMD. Además, la compatibilidad de Frigate con aceleración AMD no es tan directa como para justificar el coste técnico en este momento.

### Cómo explicarlo en la memoria

Esta decisión muestra priorización de recursos: la GPU se reserva para cargas donde aporta más valor, como Immich y Ollama, mientras que Frigate queda en CPU porque cumple el requisito sin competir por VRAM.

## Immich

Immich sí utiliza la GPU mediante ROCm para capacidades de machine learning asociadas a fotografías.

Función dentro de Odín:

- subida automática de fotos;
- búsqueda de fotos;
- gestión privada de galería;
- componente del bloque `Pensar` de Odín, al permitir recuperar recuerdos visuales.

## Ollama

Ollama está instalado como servicio systemd y se ha usado con GPU AMD/ROCm. En la inspección inicial el servicio aparecía parado, pero los logs muestran ejecución previa con detección de memoria AMD y un runner terminado por `killed`, probablemente relacionado con presión de memoria o carga del modelo.

Esto debe conectarse con los riesgos previstos:

- saturación de VRAM;
- inestabilidad del stack AMD/ROCm;
- necesidad de gestionar qué modelos quedan residentes;
- posible fallback o reinicio controlado.

El 2026-05-07 se levantó de nuevo con `systemctl start ollama` y la API respondió correctamente en `/api/tags`. Se creó además `odin_autorepair.py`, una herramienta conservadora que diagnostica Ollama, GPU, Docker y disco, y que solo arranca Ollama automáticamente cuando está inactivo y se ejecuta con `--repair`.

## Estado general

El servidor está en una fase experimental avanzada, no en una fase limpia de producción. Hay piezas en uso, piezas descartadas y pruebas en cuarentena. Esto no es un defecto para la memoria; al contrario, permite explicar el proceso real de construcción de Odín:

1. probar alternativas;
2. medir compatibilidad;
3. descartar lo que no cumple latencia/estabilidad;
4. consolidar lo que sí funciona;
5. documentar deuda técnica y trabajo futuro.
