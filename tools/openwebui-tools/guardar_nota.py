"""
title: Archivero de Nextcloud
description: Herramienta exclusiva para guardar notas, resúmenes y documentos en Nextcloud a través de n8n.
author: Quique
version: 1.0.0
requirements: requests
"""

import requests


class Tools:
    def __init__(self):
        # Lista exacta de tus carpetas (excluyendo TheVault y SubidaInstantánea)
        self.carpetas_validas = [
            "Curiosidades",
            "Documentos Personales",
            "Garantías",
            "Ideas Proyectos",
            "Libros",
            "Otros",
            "Photos",
            "Procesados",
            "Recetas",
            "Viajes",
        ]

    def guardar_nota_nextcloud(
        self, carpeta: str, titulo_archivo: str, contenido_markdown: str
    ) -> str:
        """
        [USO OBLIGATORIO PARA ARCHIVAR] Guarda una nota en Nextcloud.
        Úsalo cuando Quique te pida guardar un resumen, artículo, receta o idea.

        :param carpeta: Debe ser una de estas: "Curiosidades", "Documentos Personales", "Garantías", "Ideas Proyectos", "Libros", "Otros", "Photos", "Procesados", "Recetas", "Viajes".
        :param titulo_archivo: Nombre limpio acabado en .md (ej: "resumen-metal-slug.md").
        :param contenido_markdown: Contenido redactado en formato Markdown.
        """
        # VALIDACIÓN: Si la carpeta que elige Odín no está en tu lista, forzamos "Otros"
        if carpeta not in self.carpetas_validas:
            carpeta = "Otros"

        # Aseguramos la extensión del archivo
        if not titulo_archivo.endswith(".md"):
            titulo_archivo += ".md"

        url = (
            "https://<N8N_PUBLIC_HOST>/webhook/<WEBHOOK_ID>"
        )

        payload = {
            "carpeta": carpeta,
            "titulo_archivo": titulo_archivo,
            "contenido_markdown": contenido_markdown,
        }

        try:
            # Añadimos un timeout para que la interfaz no se quede colgada si falla
            response = requests.post(url, json=payload, timeout=15)

            if response.status_code == 200:
                return f"Nota archivada correctamente en la carpeta: {carpeta} con el nombre {titulo_archivo}"
            else:
                return f"Error {response.status_code} al contactar con n8n. Revisa el workflow."

        except Exception as e:
            return f"Error de conexión con n8n: {str(e)}"
