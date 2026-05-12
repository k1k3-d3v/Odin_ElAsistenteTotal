# Open WebUI tools de Odín (export saneado)

Este directorio contiene una copia saneada de las herramientas reales de Open WebUI usadas por Odín.

- Los ficheros `.py` contienen la lógica de las tools con URLs privadas, tokens, API keys y webhook IDs sustituidos por placeholders.
- Los ficheros `.spec.json` contienen las especificaciones funcionales exportadas desde Open WebUI.
- No se versionan `valves`, credenciales reales ni secretos.

Para restaurar una tool en una instancia real hay que reconfigurar manualmente los valores sensibles desde variables, valves o `.env`.
