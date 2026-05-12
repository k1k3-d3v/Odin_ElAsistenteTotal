# Docker Compose de Odín (versiones saneadas)

Este directorio contiene copias saneadas de los stacks Docker activos de Odín.

Stacks incluidos:

- `odin-master`: Open WebUI, Qdrant, Nextcloud, n8n, Evolution API, Cloudflared, Crawl4AI y Stirling PDF.
- `immich`: servidor, PostgreSQL, Redis/Valkey y machine learning.
- `audio`: Piper, faster-whisper, Wyoming Whisper y ASR propio.
- `frigate`: videovigilancia.
- `home-assistant-proxy`: proxy hacia Home Assistant en Raspberry Pi 5.
- `netdata`: monitorización visual.
- `pocket-tts-openai_streaming_server`: TTS experimental.

Los ficheros no contienen credenciales reales. Los valores sensibles aparecen como `${VARIABLE:?set in .env}` o placeholders equivalentes. Antes de desplegar hay que crear el `.env` correspondiente en el servidor.
