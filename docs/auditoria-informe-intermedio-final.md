# Auditoría del informe intermedio frente a la memoria final

Fecha de revisión: 9 de junio de 2026.

Esta auditoría verifica que el contenido relevante de `informe-seguimiento/`
está recogido en la memoria final. Cuando una afirmación quedó obsoleta, se
conserva su valor histórico y se documenta el estado final más reciente.

| Bloque intermedio | Destino final | Tratamiento |
|---|---|---|
| Contexto, motivación y valor diferencial | Capítulos 3 y 4 | Integrado y ampliado. |
| Objetivos, alcance y requisitos | Capítulo 5 | Integrado; añadidos dispositivos opcionales y estado real. |
| Planificación y dedicación | Capítulo 7 | Añadida la fotografía histórica de 425 horas y sus desviaciones. |
| Metodología y rigor | Capítulo 6 | Añadido el ciclo de cinco pasos, cambios reversibles y pruebas por capas. |
| VPN y acceso remoto | Capítulo 10 | Integrado; añadidos los bloqueos amplios y las rutas alternativas. |
| Alternativas de voz | Capítulo 11 | Integrado y actualizado con la solución vigente. |
| Servicios especializados frente a monolito | Capítulo 4 | Justificación explícita añadida. |
| CPU, GPU y AMD/ROCm | Capítulos 10, 11 y 12 | Integrado con pruebas y limitaciones. |
| Home Assistant en Docker, VM y Raspberry Pi | Capítulo 11 | Añadida la evolución de la decisión. |
| Competencias CTI1.3, CTI2.3 y CTI3.1 | Capítulo 13 | Añadida una tabla de evidencias. |
| RGPD, LOPDGDD y videovigilancia | Capítulo 10 | Añadido el marco normativo y sus referencias. |
| Implicación profesional, ética e iniciativa | Capítulo 13 | Añadida una sección específica. |
| Estimación económica revisada | Capítulo 8 | Añadidos costes, contingencia y fórmulas de desviación. |
| Riesgos reformulados | Capítulo 7 | Añadidos deuda operativa, automatizaciones, secretos, GPU y backup. |
| Estado funcional intermedio | Capítulos 11 y 12 | Sustituido por el estado verificado más reciente. |
| Herramientas de Open WebUI | Capítulo 11 y Anexo A | Distingue herramientas vigentes, históricas y conectores retirados. |
| Decisiones provisionales de TTS | Capítulos 11 y 12 | Conservadas como evaluación; prevalece el motor operativo final. |
| Consumo y backup | Capítulos 5, 7, 8, 9, 12 y 13 | Enchufes integrados; NVMe montado por UUID y repositorio Restic cifrado con restauración validada. |

## Criterio de consistencia

La memoria final prevalece cuando existe una diferencia temporal. El informe
intermedio describe una instantánea; la memoria final incorpora el cambio de
red, nombres locales, restauración de servicios, Mealie, herramientas
conversacionales, Frigate, voz y la situación real de consumo y backup.

No se han trasladado secretos, claves API, contraseñas ni tokens. Las
credenciales aparecen únicamente como procedimientos de rotación, variables de
entorno y ejemplos sanitizados.
