# Comparativa de VPN y capa de voz

## Acceso remoto

Odín necesita acceso remoto seguro sin exponer servicios internos a Internet. Se comparan tres alternativas:

| Criterio | OpenVPN | WireGuard | Tailscale |
| --- | --- | --- | --- |
| Base técnica | SSL/TLS, certificados y perfiles | Protocolo moderno con claves públicas | WireGuard más coordinación, identidad y NAT traversal |
| Configuración | Alta | Media | Baja |
| DNS dinámico | Normalmente necesario si no hay IP fija | Normalmente necesario si no hay IP fija | No depende de DuckDNS para localizar nodos |
| NAT traversal | Manual o mediante red bien diseñada | Manual | Integrado |
| Mantenimiento | Alto | Medio | Bajo |
| Encaje en Odín | Robusto pero pesado | Muy eficiente, pero más manual | Elegido por estabilidad y sencillez |

Decisión actual: Tailscale.

Motivo práctico: la solución anterior dependía de DuckDNS y fallaba en momentos de degradación del servicio. Tailscale evita abrir puertos, reduce dependencia de DNS dinámico y mantiene acceso al servidor mediante VPN.

## Voz: STT y TTS

La capa de voz se divide en:

- STT/ASR: audio a texto.
- TTS: texto a voz.

### STT/ASR

| Herramienta | Estado | Nota |
| --- | --- | --- |
| Whisper / faster-whisper | En pruebas/servicio | Buena precisión, CPU suficiente para algunas tareas. |
| Wyoming Whisper | En uso/prueba | Integración útil con Home Assistant. |
| Odin ONNX ASR | En uso/prueba | Servicio propio para control local. |

### TTS

| Herramienta | Estado | Nota |
| --- | --- | --- |
| Piper | En uso | Estable y rápido para físico/móvil. |
| Kokoro | Probado | No consolidado. |
| Chatterbox | Probado | Funcionó en GPU, pero demasiado lento. |
| PocketTTS | Línea actual | Compatible con estilo OpenAI, en evaluación. |

Conclusión: la voz es uno de los mayores stoppers del proyecto por la combinación de requisitos de naturalidad, baja latencia y compatibilidad AMD/ROCm.
