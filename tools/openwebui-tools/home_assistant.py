"""
title: Home Assistant Odin Edition
author: Odin & Quique
version: 4.2.0
description: Control de Midgard, calendario, compra, domótica y escáner de salud desde Home Assistant.
"""

import aiohttp
import json
import difflib
from typing import Any, Optional
from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        HA_URL: str = Field(default="http://<LAN_IP>:8123")
        HA_TOKEN: str = Field(
            default="<REDACTED_SECRET>"
        )

    def __init__(self):
        self.valves = self.Valves()

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
                method, url, headers=headers, json=data, timeout=10
            ) as response:
                if response.status >= 400:
                    text = await response.text()
                    raise Exception(f"Error {response.status}: {text}")

                try:
                    return await response.json()
                except:
                    return await response.text()

    # ==========================================================
    # SALUD Y BIENESTAR
    # ==========================================================
    async def get_health_status(self) -> str:
        """
        NOMBRE DE LA HERRAMIENTA:
        get_health_status.

        CUÁNDO USAR ESTA HERRAMIENTA:
        Usa esta herramienta siempre que Quique pregunte por su salud, estado físico,
        descanso, sueño, pasos, actividad, ritmo cardíaco, frecuencia cardíaca, calorías,
        peso, SpO2, métricas corporales o datos recogidos desde Wear OS, Health Connect
        o sensores de salud en Home Assistant.

        También debes usarla cuando Quique diga cosas como:
        cómo estoy hoy.
        cómo he dormido.
        cuántos pasos llevo.
        mira mi salud.
        mira mis datos de salud.
        cómo voy de actividad.
        qué tal mi descanso.
        revisa mi sueño.
        revisa mi frecuencia cardíaca.
        revisa mis calorías.
        qué datos de salud tienes.

        QUÉ HACE:
        Consulta todos los estados de Home Assistant y filtra sensores relacionados con
        salud, pasos, sueño, frecuencia cardíaca, calorías, peso, actividad y métricas
        similares.

        REGLA CRÍTICA PARA EL MODELO:
        Antes de usar esta herramienta, lee a fondo esta descripción.
        No inventes datos de salud.
        No des consejos médicos como diagnóstico.
        Usa únicamente los datos devueltos por la herramienta.
        Si la herramienta devuelve datos en crudo, interprétalos de forma natural para Quique.
        Si no hay datos, dilo claramente.
        Si hay error, informa del error.

        CUÁNDO NO USARLA:
        No la uses para controlar luces, sensores normales, clima o enchufes.
        No la uses para calendario.
        No la uses para lista de la compra.
        No la uses para cámaras.
        No la uses para notas.

        PARÁMETROS:
        No necesita parámetros.

        RESPUESTA ESPERADA:
        Devuelve una lista de sensores de salud encontrados.
        El modelo debe convertir esos datos en un resumen breve y humano.
        """
        try:
            states = await self._make_request("GET", "states")

            health_keywords = [
                "step",
                "pasos",
                "sleep",
                "sueño",
                "heart",
                "corazon",
                "frecuencia",
                "bpm",
                "calori",
                "health",
                "salud",
                "spo2",
                "peso",
                "weight",
                "activity",
            ]

            health_data = []
            for s in states:
                eid = s["entity_id"].lower()
                name = s.get("attributes", {}).get("friendly_name", "").lower()

                if eid.startswith("sensor."):
                    if any(kw in eid or kw in name for kw in health_keywords):
                        friendly_name = s.get("attributes", {}).get(
                            "friendly_name", eid
                        )
                        state = s.get("state", "Desconocido")
                        unit = s.get("attributes", {}).get("unit_of_measurement", "")

                        if state not in ["unknown", "unavailable"]:
                            health_data.append(
                                f"{friendly_name}: {state} {unit}".strip()
                            )

            if not health_data:
                return "No he encontrado datos de salud en Home Assistant. Dile a Quique que compruebe que la app de Wear OS o Health Connect está enviando los sensores a Midgard."

            return (
                "ATENCIÓN ODÍN. DATOS DE SALUD ENCONTRADOS:\n"
                + "\n".join(health_data)
                + "\n\nTu tarea: Interpreta estos datos en crudo y hazle un resumen natural y humano a Quique sobre su actividad y descanso de hoy."
            )

        except Exception as e:
            return f"Error en Midgard al leer la salud: {str(e)}"

    # ==========================================================
    # COMPRA
    # ==========================================================
    async def manage_shopping_list(self, action: str, item: str = "") -> str:
        """
        NOMBRE DE LA HERRAMIENTA:
        manage_shopping_list.

        CUÁNDO USAR ESTA HERRAMIENTA:
        Usa esta herramienta obligatoriamente cuando Quique mencione la lista de la compra,
        comprar, adquirir, añadir, borrar, quitar, eliminar, leer, consultar, supermercado,
        súper, alimentos, despensa o productos que haya que comprar.

        Esta es la única herramienta permitida para la lista de la compra.

        REGLA CRÍTICA PARA EL MODELO:
        Antes de usar esta herramienta, lee a fondo esta descripción.
        Está total y estrictamente prohibido usar control_home_assistant para cualquier cosa
        relacionada con la lista de la compra.
        No uses otra herramienta para compra.
        No simules haber añadido, borrado o leído la lista si no has llamado a esta herramienta.

        ACCIONES DISPONIBLES:
        action igual a "add":
        Añade un producto a la lista.
        Debes rellenar item con el producto exacto que Quique quiere añadir.

        action igual a "delete":
        Borra un producto de la lista.
        Debes rellenar item con el producto exacto que Quique quiere borrar.

        action igual a "read":
        Lee los productos pendientes de la lista.
        En este caso item puede quedar vacío.

        CUÁNDO USAR CADA ACCIÓN:
        Si Quique pide añadir algo, usa action "add".
        Si Quique pide borrar, quitar o eliminar algo, usa action "delete".
        Si Quique pregunta qué hay que comprar, qué hay en la lista o quiere consultar la lista, usa action "read".

        PARÁMETROS:
        action: debe ser exactamente "add", "delete" o "read".
        item: producto que se añade o borra. Solo es necesario para add y delete.

        EJEMPLOS:
        Quique dice: añade leche a la lista.
        Usa action "add" e item "leche".

        Quique dice: borra pan de la lista.
        Usa action "delete" e item "pan".

        Quique dice: qué hay en la lista de la compra.
        Usa action "read" e item vacío.

        RESPUESTA ESPERADA:
        Si añade, confirma que el producto se ha añadido.
        Si borra, confirma que el producto se ha borrado.
        Si lee, interpreta los datos crudos y responde con naturalidad.
        Si la lista está vacía, di que está vacía.
        """
        action = action.lower().strip()
        entity_id = "todo.lista_de_la_compra"

        try:
            if action == "add":
                data = {"entity_id": entity_id, "item": item}
                await self._make_request("POST", "services/todo/add_item", data)
                return f"Hecho. He añadido {item} a la lista."

            elif action == "delete":
                data = {"entity_id": entity_id, "item": item}
                await self._make_request("POST", "services/todo/remove_item", data)
                return f"Hecho. He borrado {item} de la lista."

            elif action == "read":
                data = {"entity_id": entity_id, "status": ["needs_action"]}
                response = await self._make_request(
                    "POST", "services/todo/get_items?return_response=true", data
                )
                return f"ATENCIÓN ODÍN. DATOS CRUDOS DE LA LISTA: {json.dumps(response)}. Tu tarea: Lee el campo summary de los elementos y díselos a Quique con naturalidad. Si ves que no hay items o el diccionario está vacío, dile que la lista está vacía."

            else:
                return "Acción no válida. Usa add, delete o read."

        except Exception as e:
            return f"Error en Midgard: {str(e)}"

    # ==========================================================
    # CALENDARIO
    # ==========================================================
    async def manage_calendar(
        self,
        titulo: str,
        fecha: str,
        hora_inicio: str,
        hora_fin: str,
        descripcion: str = "",
    ) -> str:
        """
        NOMBRE DE LA HERRAMIENTA:
        manage_calendar.

        CUÁNDO USAR ESTA HERRAMIENTA:
        Usa esta herramienta cuando Quique pida crear un evento, añadir una cita,
        apuntar algo en el calendario, recordar algo, poner un recordatorio,
        guardar una fecha, agendar una tarea o crear una entrada temporal.

        También debes usarla cuando Quique diga cosas como:
        recuérdame.
        apunta.
        pon en el calendario.
        crea un evento.
        añade una cita.
        avísame de.
        agenda.
        guarda esto para mañana.
        acuérdate de.

        QUÉ HACE:
        Crea un evento en el calendario de Home Assistant.

        REGLA CRÍTICA PARA EL MODELO:
        Antes de usar esta herramienta, lee a fondo esta descripción.
        Debes calcular correctamente fecha, hora de inicio y hora de fin.
        Nunca pongas la misma hora de inicio y hora de fin.
        Si Quique no indica hora de fin, calcula una hora de fin razonable posterior.
        Para recordatorios simples, usa una duración breve pero válida.
        No digas que has creado un evento si no has usado esta herramienta.

        PARÁMETROS:
        titulo: nombre claro del evento.
        fecha: debe ser una sola palabra. Valores válidos:
        hoy.
        mañana.
        manana.
        lunes.
        martes.
        miércoles.
        miercoles.
        jueves.
        viernes.
        sábado.
        sabado.
        domingo.

        hora_inicio: hora de inicio en formato HH:MM.
        hora_fin: hora de fin en formato HH:MM.
        descripcion: texto opcional con detalles del evento.

        IMPORTANTE SOBRE FECHAS:
        Esta herramienta no acepta fechas completas como 2026-05-06.
        El parámetro fecha debe ser una palabra válida como hoy, mañana o un día de la semana.
        El sistema calcula la fecha real automáticamente usando la zona horaria de España.

        IMPORTANTE SOBRE HORAS:
        hora_inicio y hora_fin deben estar en formato HH:MM.
        hora_fin debe ser posterior a hora_inicio.
        No uses la misma hora para inicio y fin.

        EJEMPLOS:
        Quique dice: recuérdame mañana a las 20 comprar pan.
        Usa titulo "Comprar pan", fecha "mañana", hora_inicio "20:00", hora_fin "20:15".

        Quique dice: crea un evento el viernes de 18 a 20, dentista.
        Usa titulo "Dentista", fecha "viernes", hora_inicio "18:00", hora_fin "20:00".

        Quique dice: apunta hoy a las 21 llamar a Ivet.
        Usa titulo "Llamar a Ivet", fecha "hoy", hora_inicio "21:00", hora_fin "21:15".

        CUÁNDO NO USARLA:
        No la uses para lista de la compra.
        No la uses para controlar casa.
        No la uses para notas.
        No la uses para cámaras.
        """
        from datetime import datetime, timedelta

        try:
            from zoneinfo import ZoneInfo

            tz_spain = ZoneInfo("Europe/Madrid")
        except ImportError:
            from datetime import timezone

            tz_spain = timezone(timedelta(hours=2))

        now = datetime.now(tz_spain)
        target_date = now.date()
        fecha_clean = fecha.lower().strip()

        dias = {
            "lunes": 0,
            "martes": 1,
            "miércoles": 2,
            "miercoles": 2,
            "jueves": 3,
            "viernes": 4,
            "sábado": 5,
            "sabado": 5,
            "domingo": 6,
        }

        if fecha_clean in ["mañana", "manana"]:
            target_date += timedelta(days=1)
        elif fecha_clean in dias:
            target_weekday = dias[fecha_clean]
            current_weekday = target_date.weekday()
            days_ahead = target_weekday - current_weekday
            if days_ahead <= 0:
                days_ahead += 7
            target_date += timedelta(days=days_ahead)
        elif fecha_clean != "hoy":
            return "Odín, te has equivocado al pasar el parámetro fecha. Usa hoy, mañana o un día de la semana."

        try:
            h_in, m_in = map(int, hora_inicio.split(":"))
            h_fin, m_fin = map(int, hora_fin.split(":"))

            dt_inicio = datetime.combine(target_date, datetime.min.time()).replace(
                hour=h_in, minute=m_in, tzinfo=tz_spain
            )
            dt_fin = datetime.combine(target_date, datetime.min.time()).replace(
                hour=h_fin, minute=m_fin, tzinfo=tz_spain
            )

            if dt_fin <= dt_inicio:
                return "Odín, la hora de fin debe ser posterior a la hora de inicio. Nunca uses la misma hora de inicio y fin."

        except ValueError:
            return "Error de formato de hora. Usa HH:MM."

        data = {
            "entity_id": "calendar.mycal",
            "summary": titulo,
            "start_date_time": dt_inicio.isoformat(),
            "end_date_time": dt_fin.isoformat(),
        }

        if descripcion:
            data["description"] = descripcion

        try:
            await self._make_request("POST", "services/calendar/create_event", data)
            return f"Hecho Quique. Evento '{titulo}' añadido para el {target_date.strftime('%d/%m/%Y')} de {hora_inicio} a {hora_fin} hora de España."
        except Exception as e:
            return f"Error en el calendario: {str(e)}"

    # ==========================================================
    # DOMÓTICA
    # ==========================================================
    async def control_home_assistant(self, user_request: str) -> dict:
        """
        NOMBRE DE LA HERRAMIENTA:
        control_home_assistant.

        CUÁNDO USAR ESTA HERRAMIENTA:
        Usa esta herramienta cuando Quique quiera buscar, consultar o controlar dispositivos
        de Home Assistant como luces, sensores, enchufes, interruptores, clima, temperatura,
        persianas, habitaciones, aparatos o entidades domóticas.

        Esta herramienta sirve para encontrar la entidad adecuada antes de ejecutar una acción.

        QUÉ HACE:
        Consulta los estados de Home Assistant y busca entidades cuyo nombre coincida con
        la petición de Quique.

        REGLA CRÍTICA PARA EL MODELO:
        Antes de usar esta herramienta, lee a fondo esta descripción.
        Esta herramienta solo busca entidades candidatas.
        Para ejecutar una acción real sobre una entidad, después debes usar execute_action.
        No digas que has encendido, apagado o cambiado algo si solo has usado esta herramienta.
        No inventes entity_id.
        Usa los resultados devueltos para elegir la entidad correcta.

        PROHIBICIÓN ABSOLUTA:
        No uses esta herramienta para la lista de la compra.
        Si Quique menciona comprar, lista de la compra, alimentos, supermercado o productos
        del súper, usa manage_shopping_list, no control_home_assistant.

        PARÁMETROS:
        user_request: petición natural de Quique, por ejemplo "enciende la luz del salón".

        EJEMPLOS:
        Quique dice: enciende la luz del salón.
        Primero usa control_home_assistant con user_request "enciende la luz del salón".
        Después usa execute_action con la entidad correcta y el servicio adecuado.

        Quique dice: apaga el enchufe del escritorio.
        Primero usa control_home_assistant.
        Después usa execute_action.

        Quique dice: qué temperatura hay en casa.
        Usa control_home_assistant para buscar el sensor adecuado.
        Si solo es consulta, responde con el estado si está disponible en los resultados o usa la información de la entidad encontrada.

        CUÁNDO NO USARLA:
        No la uses para compra.
        No la uses para calendario.
        No la uses para salud si Quique pide métricas de salud generales. Para eso usa get_health_status.
        No la uses para cámaras.
        No la uses para notas.
        """
        states = await self._make_request("GET", "states")

        scored = []
        for s in states:
            eid = s["entity_id"]
            name = s.get("attributes", {}).get("friendly_name", eid)
            score = difflib.SequenceMatcher(
                None, user_request.lower(), name.lower()
            ).ratio()

            if score > 0.4:
                scored.append({"entity_id": eid, "name": name, "score": score})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return {"results": scored[:5]}

    async def execute_action(
        self, entity_id: str, service: str, metadata: Optional[str] = None
    ) -> dict:
        """
        NOMBRE DE LA HERRAMIENTA:
        execute_action.

        CUÁNDO USAR ESTA HERRAMIENTA:
        Usa esta herramienta para ejecutar una acción real sobre una entidad de Home Assistant
        después de haber identificado la entidad correcta.

        Debes usarla para acciones como:
        encender una luz.
        apagar una luz.
        cambiar brillo.
        cambiar color.
        encender un enchufe.
        apagar un enchufe.
        activar un interruptor.
        desactivar un interruptor.
        ajustar clima.
        ejecutar un servicio de Home Assistant sobre una entidad.

        QUÉ HACE:
        Llama a un servicio de Home Assistant sobre un entity_id concreto.

        REGLA CRÍTICA PARA EL MODELO:
        Antes de usar esta herramienta, lee a fondo esta descripción.
        No uses execute_action si no tienes claro el entity_id.
        No inventes entity_id.
        No inventes servicios.
        Normalmente debes usar control_home_assistant antes para encontrar la entidad.
        Después usa execute_action para ejecutar la acción.

        PARÁMETROS:
        entity_id: entidad exacta de Home Assistant, por ejemplo light.salon.
        service: servicio que se quiere ejecutar, por ejemplo turn_on, turn_off, light.turn_on o switch.turn_off.
        metadata: JSON opcional en texto para parámetros adicionales, como brillo, color o temperatura.

        EJEMPLOS:
        Para encender una luz:
        entity_id "light.salon".
        service "turn_on".

        Para apagar una luz:
        entity_id "light.salon".
        service "turn_off".

        Para cambiar brillo:
        entity_id "light.salon".
        service "turn_on".
        metadata "{\"brightness_pct\": 50}".

        Para cambiar temperatura de color:
        entity_id "light.salon".
        service "turn_on".
        metadata "{\"color_temp_kelvin\": 3000}".

        CUÁNDO NO USARLA:
        No la uses para lista de la compra.
        No la uses para calendario.
        No la uses para guardar notas.
        No la uses para buscar documentos.
        No la uses para cámaras.
        """
        domain = entity_id.split(".")[0]
        actual_service = service.split(".")[-1]

        data = {"entity_id": entity_id}

        if metadata:
            data.update(json.loads(metadata))

        await self._make_request("POST", f"services/{domain}/{actual_service}", data)
        return {"status": "ok"}
