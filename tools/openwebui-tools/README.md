# Open WebUI tools de Odín

Este directorio contiene el catálogo saneado de las herramientas reales de
Open WebUI usadas por Odín.

- `index.json` enumera las tools, funciones y estado de asignación a Odín.
- La explicación completa está en
  `docs/estado-final-tools-integraciones-2026-06-09.md`.
- El código vivo permanece en la base de datos de Open WebUI y en los proxies
  del servidor.
- No se versionan valves, credenciales reales, tokens ni secretos.

Para restaurar una tool en otra instancia hay que exportar su código desde
Open WebUI y reconfigurar manualmente los valores sensibles mediante variables,
valves o `.env`.
