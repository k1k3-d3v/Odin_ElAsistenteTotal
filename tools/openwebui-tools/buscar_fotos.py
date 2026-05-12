import requests


class Tools:
    def __init__(self):
        pass

    def buscar_foto(self, descripcion: str) -> str:
        """
        CUÁNDO USAR ESTA HERRAMIENTA:
        Usa esta herramienta cuando Quique pida buscar, ver, localizar o mostrar una foto,
        imagen, recuerdo visual, persona, lugar, objeto, animal, evento o escena que pueda
        estar guardada en Immich.

        QUÉ HACE:
        Busca en Immich una foto relacionada con la descripción indicada.
        Devuelve una imagen incrustada en formato markdown para que se vea directamente
        en el chat.

        INSTRUCCIÓN CRÍTICA PARA EL MODELO:
        Siempre que esta herramienta devuelva una imagen en formato markdown, debes mostrarla
        exactamente tal cual aparece en el resultado.

        El formato de imagen será parecido a este:
        ![foto](url)

        No cambies ese formato.
        No lo metas entre comillas.
        No lo conviertas en enlace normal.
        No lo resumas.
        No digas solo que has encontrado la foto.
        No leas la URL en voz alta.
        No elimines los paréntesis.
        No elimines los corchetes.
        No cambies el signo de exclamación inicial.

        RESPUESTA OBLIGATORIA:
        Si la herramienta devuelve una línea con ![texto](url), tu respuesta debe incluir
        esa línea completa y sin modificar, porque así la imagen se renderiza en el chat.

        PARÁMETROS:
        descripcion: texto natural que describe la foto que Quique quiere encontrar.

        EJEMPLOS DE USO:
        Quique dice: busca una foto de Thor.
        Usa esta herramienta con descripcion igual a "Thor".

        Quique dice: enséñame una foto de la playa.
        Usa esta herramienta con descripcion igual a "playa".

        Quique dice: busca recuerdos de Navidad.
        Usa esta herramienta con descripcion igual a "Navidad".

        SI NO HAY RESULTADOS:
        Informa de que no se ha encontrado ninguna foto relacionada.

        SI HAY ERROR:
        Informa del error devuelto por la herramienta.
        """
        api_url = "http://<LAN_IP>:2283/api"
        api_key = "<IMMICH_API_KEY>"
        proxy_url = "https://<N8N_PUBLIC_HOST>/webhook/<WEBHOOK_ID>"

        try:
            # Busca en Immich usando búsqueda inteligente.
            # size 1 significa que solo se devuelve la mejor coincidencia.
            r = requests.post(
                f"{api_url}/search/smart",
                json={"query": descripcion, "size": 1},
                headers={"x-api-key": "<IMMICH_API_KEY>"},
                timeout=10,
            )

            items = r.json().get("assets", {}).get("items", [])

            if not items:
                return f"No he encontrado fotos de '{descripcion}'."

            asset_id = items[0]["id"]
            img_url = f"{proxy_url}?id={asset_id}"

            # MUY IMPORTANTE:
            # El resultado incluye una imagen en markdown.
            # El modelo debe imprimir exactamente la línea ![foto](url)
            # para que la imagen se vea incrustada en el chat.
            return (
                "Muestra esta imagen exactamente tal cual, sin modificar el markdown:\n\n"
                f"![foto]({img_url})"
            )

        except Exception as e:
            return f"Error al buscar la foto: {str(e)}"
