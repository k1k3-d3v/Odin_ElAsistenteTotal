"""
title: Home Assistant Assist Bridge
author: Odin & Quique
version: 1.0.0
description: Puente directo entre Odín y el asistente conversacional de Home Assistant Assist.
"""

import aiohttp
import json
from typing import Any, Optional
from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        HA_URL: str = Field(default="http://<LAN_IP>:8123")
        HA_TOKEN: str = Field(
            default="<REDACTED_SECRET>"
        )
        ASSIST_AGENT_ID: str = Field(default="conversation.odin_ha")
        LANGUAGE: str = Field(default="es")

    def __init__(self):
        self.valves = self.Valves()
        self.conversation_id = "odin_owui_midgard"

    async def _make_request(
        self, method: str, endpoint: str, data: Optional[dict] = None
    ) -> Any:
        url = f"{self.valves.HA_URL.rstrip('/')}/api/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer <REDACTED_TOKEN>",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method, url, headers=headers, json=data, timeout=15
            ) as response:
                text = await response.text()

                if response.status >= 400:
                    raise Exception(f"Error {response.status}: {text}")

                try:
                    return json.loads(text)
                except:
                    return text

    async def ask_home_assistant_assist(
        self,
        text: str,
        conversation_id: str = "",
        agent_id: str = "",
    ) -> str:
        """
        NOMBRE DE LA HERRAMIENTA:
        ask_home_assistant_assist.

        IDENTIDAD:
        Esta herramienta conecta directamente con el asistente conversacional de Home Assistant Assist.
        Es el puente entre Odín y el cerebro domótico que ya existe dentro de Home Assistant.

        CUÁNDO USAR ESTA HERRAMIENTA:
        Usa esta herramienta cuando Quique quiera controlar o consultar dispositivos, áreas,
        sensores, luces, enchufes, clima, persianas, interruptores, escenas o automatizaciones
        usando lenguaje natural.

        También debes usarla cuando Quique diga cosas como:
        enciende la luz del salón.
        apaga la cocina.
        sube la temperatura.
        baja la persiana.
        activa la escena cine.
        qué temperatura hay en el salón.
        hay alguna ventana abierta.
        apaga todas las luces.
        pon el despacho en modo trabajo.
        dile a Home Assistant que.
        pregunta a Home Assistant.

        QUÉ HACE:
        Envía el texto natural de Quique al endpoint /api/conversation/process de Home Assistant.
        Home Assistant Assist interpreta la orden y ejecuta o responde según su propio agente,
        sus áreas, entidades, alias, frases personalizadas e intents.

        REGLA CRÍTICA PARA EL MODELO:
        Antes de usar esta herramienta, lee a fondo esta descripción.
        No intentes adivinar entity_id si puedes enviar la orden natural a Assist.
        No inventes estados de sensores.
        No digas que algo se ha ejecutado si Home Assistant no lo confirma.
        Basa tu respuesta en el texto devuelto por Home Assistant.
        Si la respuesta de Home Assistant contiene error, comunica el error.
        Si Home Assistant pide aclaración, traslada esa aclaración a Quique.

        CUÁNDO NO USAR ESTA HERRAMIENTA:
        No la uses para lista de la compra, salvo que Quique pida explícitamente que lo gestione Home Assistant Assist.
        No la uses para calendario si ya existe una herramienta específica manage_calendar.
        No la uses para salud de Quique si existe get_health_status.
        No la uses para cámaras de Frigate.
        No la uses para buscar fotos.
        No la uses para buscar notas en Nextcloud.
        No la uses para guardar notas.

        PARÁMETROS:
        text:
        Orden o pregunta en lenguaje natural que se enviará a Home Assistant Assist.

        conversation_id:
        Opcional. Identificador para mantener el contexto de conversación.
        Si queda vacío, se usa una conversación fija llamada odin_owui_midgard.

        agent_id:
        Opcional. ID del agente conversacional de Home Assistant.
        Si queda vacío, se usa el valor configurado en ASSIST_AGENT_ID.
        Por defecto es conversation.odin_ha.

        RESPUESTA ESPERADA:
        La herramienta devuelve la respuesta hablada de Home Assistant si existe.
        Si no hay respuesta hablada, devuelve el JSON crudo para diagnóstico.
        """
        payload = {
            "text": text,
            "language": self.valves.LANGUAGE,
            "agent_id": agent_id or self.valves.ASSIST_AGENT_ID,
            "conversation_id": conversation_id or self.conversation_id,
        }

        try:
            result = await self._make_request(
                "POST",
                "conversation/process",
                payload,
            )

            if not isinstance(result, dict):
                return f"Respuesta de Home Assistant: {result}"

            response = result.get("response", {})
            speech = response.get("speech", {}).get("plain", {}).get("speech", "")

            response_type = response.get("response_type", "")
            new_conversation_id = result.get("conversation_id", "")

            if new_conversation_id:
                self.conversation_id = new_conversation_id

            if speech:
                return speech

            return (
                "Home Assistant ha respondido sin texto hablado. "
                f"Tipo de respuesta: {response_type}. "
                f"Datos: {json.dumps(result, ensure_ascii=False)}"
            )

        except Exception as e:
            return f"No he podido hablar con el asistente de Home Assistant: {str(e)}"
