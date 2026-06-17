# Benchmark de IA, voz y backup

Fecha de ejecución: 12 de junio de 2026.

## Entorno

- Servidor Odín con Ubuntu 24.04.4 LTS.
- AMD Ryzen 5 5600G, 30 GiB de RAM y GPU AMD con 17.095.983.104 bytes de VRAM.
- Ollama ejecutado como servicio systemd con ROCm.
- Contexto común de 4.096 tokens, temperatura 0 y el mismo prompt anti-alucinación.
- El benchmark reproducible está en `tools/benchmark_ollama.py`.

## Modelos Ollama

El prompt proporcionaba horarios y retención del backup, pero no indicaba el
cifrado del NVMe. El comportamiento correcto era reconocer la ausencia de esa
información.

| Modelo | VRAM Ollama | Frío | Caliente | Generación | Resultado |
| --- | ---: | ---: | ---: | ---: | --- |
| `qwen3.5:4b` | 5,94 GB | 6,12 s | 1,62 s | 63,10 tokens/s en caliente | Correcto; no inventó cifrado. |
| `llama3:latest` | 5,21 GB | 2,92 s | 0,94 s | 100,37 tokens/s en caliente | Incorrecto; sugirió AES-XTS, AES-CBC o TCG Opal sin evidencia. |
| `ministral-3:14b` | 10,69 GB | 4,45 s | 1,24 s | 57,57 tokens/s en caliente | Correcto y consistente; modelo elegido para Odín. |

La prueba muestra que el modelo más rápido no fue el más fiable. El Llama 3
básico producía respuestas fluidas, pero completaba lagunas con hipótesis
plausibles. Esta tendencia a alucinar justificó no usarlo como modelo principal
para acciones y memoria personal.

### Prueba de presión de VRAM

Se cargó además `lfm2:latest`, un modelo MoE cuantizado de 23,8B. Con contexto
de 16.384 tokens:

- carga en frío: 9,39 s;
- memoria declarada por Ollama: 15,02 GB;
- VRAM total observada con `rocm-smi`: 15,45 de 17,10 GB;
- uso de GPU: 100 %;
- temperatura de unión: 63 grados.

El modelo arrancó, pero dejó solo unos 1,65 GB de margen. En la práctica no
permitía convivir con otra carga relevante de IA y aumentaba el riesgo de
terminaciones del runner. Por ello se descartó como modelo cotidiano.

## STT

Se generó una locución española controlada de 8,04 s y 31 palabras:

> Odín guarda las notas en Nextcloud y busca las fotografías en Immich. La
> copia de seguridad se ejecuta a las cuatro de la mañana y conserva tres días
> en el servidor.

| Motor | Frío | Caliente | WER normalizado | Observación |
| --- | ---: | ---: | ---: | --- |
| faster-whisper small, CPU | 9,13 s | 5,32 s | 6,5 % | Confundió Nextcloud e Immich. |
| Odin ASR, ONNX | 5,95 s | 0,55 s | 6,5 % | Mismos dos errores en nombres propios. |

Ambos recuperaron correctamente el contenido semántico. El ASR propio fue
mucho más rápido tras calentar el modelo, mientras que faster-whisper mantiene
la ventaja de madurez e integración. Los nombres de servicios privados deben
añadirse como vocabulario o *hotwords*.

## TTS

Texto de prueba: “Odín está preparado. La copia de seguridad conserva tres
días en local.”

| Motor | Primer audio | Tiempo total | Audio generado | Resultado |
| --- | ---: | ---: | ---: | --- |
| Piper, Wyoming | 0,49 s en frío; 0,05 s en caliente | 0,72 s en frío; 0,13--0,20 s en caliente | 4,18--4,24 s | Opción estable para Home Assistant. |
| PocketTTS | No expone la misma métrica de streaming | 1,81--3,80 s | 4,00--5,12 s | Más variable; se mantiene experimental. |

Piper ofrece una latencia muy inferior al tiempo real y una integración directa
con Wyoming. PocketTTS es viable y compatible con una API de estilo OpenAI,
pero su variabilidad y su manejo de fragmentos largos lo hacen menos predecible.

## Backup y restauración

El script operativo es `/home/k1k3/odin/scripts/backup_diario.sh`, versionado en
`tools/backup_diario.sh`. Utiliza Restic 0.19.0 sobre un repositorio cifrado en
`/mnt/backup_nvme/odin-restic`. La copia es incremental, deduplicada y cubre
`/home/k1k3/odin` y los 202 GB de la biblioteca de Immich. Antes de copiar,
genera un volcado consistente de la base MariaDB de Nextcloud.

La auditoría encontró que las exclusiones apuntaban a rutas antiguas. El backup
del 10 de junio ocupó 3,1 GB e incluyó parte de los datos de Nextcloud. Se
corrigió el script para excluir la ruta actual
`core/odin-master/data/nextcloud/data`.

La fase anterior con `tar.gz` se utilizó como validación preliminar y permitió
detectar exclusiones obsoletas. La solución final sustituyó ese mecanismo por
Restic para simplificar la operación y cubrir también los datos masivos.

Validaciones finales:

- integridad gzip del backup anterior: correcta;
- restauración aislada de `backup_diario.sh`: hash idéntico al original;
- copia de prueba con exclusiones nuevas: 578 MB y 37.619 entradas;
- entradas del directorio personal de Nextcloud: 0;
- NVMe Crucial de 1 TB identificado por UUID y montado en
  `/mnt/backup_nvme` con permisos restrictivos;
- repositorio Restic cifrado inicializado correctamente;
- clave de recuperación copiada fuera del servidor con permisos `0600`;
- retención configurada: 7 copias diarias, 4 semanales y 6 mensuales;
- comprobación de integridad mediante `restic check`;
- restauración aislada de un fichero y comparación de hash;
- ejecución diaria programada a las 04:00.

La política queda cerrada con una única herramienta y un procedimiento simple:
conectar el NVMe, comprobar el montaje, ejecutar el script y verificar el
snapshot. Para recuperar datos se abre el repositorio con la clave conservada
fuera del servidor y se utiliza `restic restore`.
