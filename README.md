# Proyecto Odín

Repositorio del Trabajo de Fin de Grado de Enrique de Vicente-Tutor Castillo.

Odín es un asistente personal local-first, autoalojado y proactivo. El objetivo del repositorio es reunir la memoria en LaTeX y, progresivamente, la documentación técnica, configuraciones y despliegues del ecosistema.

## Compilar

```bash
/Users/quique/.codex/plugins/cache/openai-bundled/latex-tectonic/0.1.0/bin/tectonic --outdir build main.tex
```

El PDF se generara en `build/main.pdf`.

## Bibliografía

Las referencias están en `references.bib`. Las fuentes web incluyen una nota con fecha de consulta editable para poder ajustarla cuando se revise la memoria.

## Estructura

- `main.tex`: configuración general y orden del documento.
- `chapters/`: portada, resumenes y capitulos principales.
- `appendices/`: anexos.
- `figures/`: imagenes y diagramas.
- `tables/`: tablas auxiliares si hacen falta.

## Seguridad

El repositorio es privado, pero los despliegues reales del servidor deben tratarse como si fueran públicos: credenciales en `.env`, ejemplos en `.env.example` y ningún secreto versionado.
