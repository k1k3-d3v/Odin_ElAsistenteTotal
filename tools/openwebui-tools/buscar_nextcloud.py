import requests
import json


class Tools:
    def __init__(self):
        # Usamos la IP directa de tu Ubuntu para evitar problemas de resolución de Docker.
        self.qdrant_url = "http://<LAN_IP>:6333"
        self.ollama_url = "http://<LAN_IP>:11434"
        self.collection_name = "memoria_ia"

    def buscar_en_nextcloud(self, consulta: str) -> str:
        """
        NOMBRE DE LA HERRAMIENTA:
        buscar_en_nextcloud.

        IDENTIDAD:
        Esta herramienta es el Pozo de Mimir.
        Es la fuente principal de conocimiento privado de Quique.
        Busca en sus documentos, notas, apuntes, proyectos e información guardada en Nextcloud.

        CUÁNDO USAR ESTA HERRAMIENTA:
        Usa esta herramienta obligatoriamente cuando Quique pregunte por información que pueda estar en sus notas,
        documentos personales, proyectos, apuntes o memoria privada.

        Debes usarla especialmente cuando Quique pregunte por:
        notas.
        documentos.
        apuntes.
        proyectos.
        ideas guardadas.
        información académica.
        universidad.
        temas de Controladora Aérea.
        OACI.
        Ivet.
        hacking.
        ciberseguridad.
        planes personales.
        datos que Odín deba saber.
        recuerdos escritos.
        contenido guardado en Nextcloud.
        cualquier cosa que suene a información privada ya almacenada.

        También debes usarla cuando Quique diga cosas como:
        busca en mis notas.
        mira en Nextcloud.
        consulta el Pozo de Mimir.
        qué tengo sobre esto.
        qué sabes de esto en mis archivos.
        recuérdame lo que apunté.
        busca mis apuntes de.
        tengo algo guardado sobre.

        CUÁNDO NO USAR ESTA HERRAMIENTA:
        No la uses para la lista de la compra.
        No la uses para controlar dispositivos de casa.
        No la uses para cámaras.
        No la uses para buscar fotos.
        No la uses para crear eventos o recordatorios.
        No la uses para guardar notas nuevas.
        Esta herramienta solo consulta información existente.

        REGLA CRÍTICA PARA EL MODELO:
        No respondas con conocimiento genérico cuando esta herramienta sea aplicable.
        Si Quique pregunta por algo que puede estar en sus documentos, usa esta herramienta antes de responder.
        No inventes contenido de documentos.
        No digas que algo está en sus archivos si esta herramienta no lo ha devuelto.
        No digas que has consultado Nextcloud si no has usado esta herramienta.
        Basa tu respuesta únicamente en los resultados devueltos.

        CÓMO RESPONDER DESPUÉS DE USARLA:
        Si hay resultados, resume lo encontrado de forma clara.
        Puedes mencionar la fuente si aparece en el resultado.
        Si no hay resultados, di que has consultado el Pozo de Mimir y no hay registros sobre eso.
        Si hay error técnico, informa del error sin inventar una respuesta alternativa.

        PARÁMETROS:
        consulta: pregunta o descripción en lenguaje natural de lo que Quique quiere buscar.

        EJEMPLOS DE USO:
        Quique dice: busca mis apuntes sobre OACI.
        Usa buscar_en_nextcloud con consulta igual a "apuntes sobre OACI".

        Quique dice: qué tengo sobre Ivet.
        Usa buscar_en_nextcloud con consulta igual a "Ivet".

        Quique dice: mira en mis notas lo de hacking.
        Usa buscar_en_nextcloud con consulta igual a "hacking".

        Quique dice: qué sabe Odín sobre la universidad.
        Usa buscar_en_nextcloud con consulta igual a "universidad".

        Quique dice: consulta el Pozo de Mimir sobre controladora aérea.
        Usa buscar_en_nextcloud con consulta igual a "controladora aérea".

        FORMATO DEL RESULTADO:
        La herramienta devuelve fragmentos encontrados en documentos, con su fuente cuando está disponible.
        El modelo debe leer esos fragmentos y responder a Quique basándose en ellos.

        PRIORIDAD:
        Esta herramienta tiene prioridad sobre una respuesta genérica siempre que la petición pueda referirse
        a conocimiento privado, notas, documentos o memoria guardada.
        """
        try:
            # 1. Generar embeddings con el modelo mxbai.
            # Este vector representa semánticamente la consulta de Quique.
            res_emb = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": "mxbai-embed-large", "prompt": consulta},
                timeout=10,
            )
            res_emb.raise_for_status()
            vector = res_emb.json()["embedding"]

            # 2. Buscar en la base de datos vectorial Qdrant.
            # limit 5 mantiene la respuesta breve y útil para voz.
            # score_threshold 0.45 permite recuperar resultados relacionados sin ser demasiado restrictivo.
            res_qdrant = requests.post(
                f"{self.qdrant_url}/collections/{self.collection_name}/points/search",
                json={
                    "vector": vector,
                    "limit": 5,
                    "with_payload": True,
                    "score_threshold": 0.45,
                },
                timeout=10,
            )
            res_qdrant.raise_for_status()

            resultados = res_qdrant.json().get("result", [])
            if not resultados:
                return "He consultado el Pozo de Mimir pero no hay registros sobre eso en tus archivos."

            contexto = "He encontrado esto en tus documentos:\n\n"

            for res in resultados:
                p = res["payload"]
                score = round(res.get("score", 0) * 100, 1)
                fuente = p.get("metadata", {}).get("source", "Archivo desconocido")

                # Filtra fuentes que no deben contaminar la memoria semántica general.
                if any(
                    x in fuente.lower()
                    for x in ["lista de la compra", "ruido_temporal"]
                ):
                    continue

                # Limita el fragmento para que Odín no se enrolle demasiado al hablar.
                texto = p.get("text", "").strip()[:400]

                contexto += (
                    f"Fuente, {fuente}. Coincidencia, {score} por ciento. {texto}\n\n"
                )

            return contexto

        except Exception as e:
            return f"El Bifrost está bloqueado. Error técnico: {str(e)}"
