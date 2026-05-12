import requests
import time


class Tools:
    def __init__(self):
        self.frigate_url = "http://<LAN_IP>:5001/api"

    def consultar_camaras(self) -> str:
        """
        CUÁNDO USAR ESTA HERRAMIENTA:
        Usa esta función cuando Quique pregunte qué cámaras hay, qué cámaras están disponibles,
        qué cámaras están conectadas o cuando quiera ver una cámara pero no haya dado el nombre
        exacto de la cámara.

        También debes usarla si Quique pide ver una cámara con un nombre ambiguo y no sabes
        qué nombre interno tiene en Frigate.

        QUÉ HACE:
        Consulta Frigate y devuelve la lista de cámaras conectadas.

        INSTRUCCIÓN PARA EL MODELO:
        Antes de usar cualquier función de Frigate, lee a fondo su descripción.
        Si no sabes el nombre exacto de la cámara, usa primero consultar_camaras.
        No inventes nombres de cámaras.
        No expliques lo que vas a hacer.
        Muestra directamente el resultado.

        PARÁMETROS:
        No necesita parámetros.

        RESPUESTA ESPERADA:
        Devuelve una frase con las cámaras conectadas.

        EJEMPLOS DE USO:
        Quique dice: qué cámaras hay.
        Usa consultar_camaras.

        Quique dice: dime las cámaras conectadas.
        Usa consultar_camaras.

        Quique dice: quiero ver una cámara pero no sé cómo se llama.
        Usa consultar_camaras.
        """
        try:
            response = requests.get(f"{self.frigate_url}/stats", timeout=5)
            stats = response.json()
            camaras = list(stats["cameras"].keys())
            return f"Cámaras conectadas: {', '.join(camaras)}."
        except Exception as e:
            return f"Error de conexión: {str(e)}"

    def ver_foto_actual(self, camara: str) -> str:
        """
        CUÁNDO USAR ESTA HERRAMIENTA:
        Usa esta función cuando Quique pida ver una cámara ahora mismo, ver qué está pasando,
        mostrar la imagen actual, ver la vista en directo, revisar una estancia en tiempo real
        o mirar una cámara concreta.

        QUÉ HACE:
        Devuelve la imagen más reciente de una cámara de Frigate.
        Es una captura actual, no un evento antiguo.

        INSTRUCCIÓN CRÍTICA PARA EL MODELO:
        Esta función devuelve una imagen en formato markdown.
        Siempre debes mostrar la línea de imagen exactamente tal cual aparece en el resultado.

        El formato será parecido a este:
        ![camara](url)

        No cambies ese formato.
        No lo conviertas en enlace normal.
        No lo resumas.
        No lo metas entre comillas.
        No elimines el signo de exclamación.
        No elimines los corchetes.
        No elimines los paréntesis.
        No leas la URL en voz alta.
        No digas solo que la imagen está disponible.
        Debes incluir el markdown de imagen para que se renderice en el chat.

        PARÁMETROS:
        camara: nombre exacto de la cámara en Frigate.

        IMPORTANTE:
        Si Quique no da el nombre exacto de la cámara, o el nombre es ambiguo,
        usa primero consultar_camaras.
        No inventes el nombre de la cámara.

        RESPUESTA OBLIGATORIA:
        Si el resultado contiene ![texto](url), envíalo exactamente tal cual.

        EJEMPLOS DE USO:
        Quique dice: enséñame el salón ahora.
        Usa ver_foto_actual si sabes que la cámara del salón se llama tapo_salon.
        Si no lo sabes, usa primero consultar_camaras.

        Quique dice: mira la cámara tapo_salon.
        Usa ver_foto_actual con camara igual a "tapo_salon".

        Quique dice: qué pasa ahora en la entrada.
        Usa ver_foto_actual si conoces el nombre exacto de la cámara de entrada.
        Si no lo conoces, usa consultar_camaras.
        """
        timestamp = int(time.time())
        url = f"{self.frigate_url}/{camara}/latest.jpg?h=500&t={timestamp}"

        return f"Aquí tienes la vista actual de {camara}:\n\n![{camara}]({url})"

    def ver_ultimo_evento(self, camara: str) -> str:
        """
        CUÁNDO USAR ESTA HERRAMIENTA:
        Usa esta función cuando Quique pida ver el último evento, la última detección,
        el último movimiento, la última persona detectada, la última captura grabada
        o qué ha pasado recientemente en una cámara concreta.

        QUÉ HACE:
        Consulta Frigate y devuelve la imagen del último evento detectado en la cámara indicada.
        Esto no es una imagen en vivo. Es el último evento grabado.

        INSTRUCCIÓN CRÍTICA PARA EL MODELO:
        Esta función puede devolver una imagen en formato markdown.
        Siempre debes mostrar la línea de imagen exactamente tal cual aparece en el resultado.

        El formato será parecido a este:
        ![Evento](url)

        No cambies ese formato.
        No lo conviertas en enlace normal.
        No lo resumas.
        No lo metas entre comillas.
        No elimines el signo de exclamación.
        No elimines los corchetes.
        No elimines los paréntesis.
        No leas la URL en voz alta.
        No digas solo que hay una detección.
        Debes incluir el markdown de imagen para que se renderice en el chat.

        PARÁMETROS:
        camara: nombre exacto de la cámara en Frigate.

        IMPORTANTE:
        Si Quique no da el nombre exacto de la cámara, o el nombre es ambiguo,
        usa primero consultar_camaras.
        No inventes el nombre de la cámara.

        RESPUESTA OBLIGATORIA:
        Si el resultado contiene ![texto](url), envíalo exactamente tal cual.

        EJEMPLOS DE USO:
        Quique dice: enséñame el último movimiento del salón.
        Usa ver_ultimo_evento si sabes que la cámara del salón se llama tapo_salon.
        Si no lo sabes, usa primero consultar_camaras.

        Quique dice: última detección de tapo_salon.
        Usa ver_ultimo_evento con camara igual a "tapo_salon".

        Quique dice: ha pasado algo en la entrada.
        Usa ver_ultimo_evento si la intención es revisar una detección reciente.
        Si quiere ver el directo, usa ver_foto_actual.
        """
        try:
            response = requests.get(
                f"{self.frigate_url}/events?camera={camara}&limit=1", timeout=5
            )
            eventos = response.json()
            if not eventos:
                return f"No hay eventos grabados en {camara}."

            ev = eventos[0]
            event_id = ev["id"]
            label = ev["label"]
            snapshot_url = f"{self.frigate_url}/events/{event_id}/snapshot.jpg"

            return f"Detección de {label} en {camara}:\n\n![Evento]({snapshot_url})"
        except Exception as e:
            return f"Error al recuperar evento: {str(e)}"
