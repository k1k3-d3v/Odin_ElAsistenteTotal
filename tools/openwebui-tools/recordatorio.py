import requests
from datetime import datetime, timedelta


class Tools:
    def __init__(self):
        pass

    def anadir_evento_calendario(
        self,
        titulo: str,
        descripcion: str,
        dia_relativo: str,
        hora_inicio_HH_MM: str,
        hora_fin_HH_MM: str,
    ) -> str:
        """
        Crea un evento en el calendario.
        NO INTENTES CALCULAR LA FECHA EXACTA.

        :param titulo: Título del evento (ej: "Cena Sant Jordi").
        :param descripcion: Breve descripción.
        :param dia_relativo: Solo puedes usar una de estas opciones exactas: "hoy", "mañana", "pasado mañana", o el nombre de un día de la semana si es para la semana que viene (ej: "lunes", "martes", etc).
        :param hora_inicio_HH_MM: Hora de inicio en formato 'HH:MM' (ej: '21:00').
        :param hora_fin_HH_MM: Hora de fin en formato 'HH:MM' (ej: '22:00').
        """

        # 1. Obtenemos el día de hoy
        hoy = datetime.now()
        fecha_objetivo = hoy

        # 2. El script de Python hace las matemáticas que la IA no sabe hacer
        dia_relativo = dia_relativo.lower().strip()

        if dia_relativo == "mañana":
            fecha_objetivo = hoy + timedelta(days=1)
        elif dia_relativo == "pasado mañana":
            fecha_objetivo = hoy + timedelta(days=2)
        elif dia_relativo in [
            "lunes",
            "martes",
            "miércoles",
            "miercoles",
            "jueves",
            "viernes",
            "sábado",
            "sabado",
            "domingo",
        ]:
            # Calcular cuántos días faltan para ese día de la semana
            dias_semana = [
                "lunes",
                "martes",
                "miércoles",
                "jueves",
                "viernes",
                "sábado",
                "domingo",
            ]
            # Ajuste sin tildes para simplificar
            dias_semana_limpios = [
                "lunes",
                "martes",
                "miercoles",
                "jueves",
                "viernes",
                "sabado",
                "domingo",
            ]

            # Buscar el índice del día actual y del día objetivo
            idx_hoy = hoy.weekday()

            try:
                idx_objetivo = dias_semana.index(dia_relativo)
            except ValueError:
                idx_objetivo = dias_semana_limpios.index(dia_relativo)

            dias_diferencia = idx_objetivo - idx_hoy
            if dias_diferencia <= 0:
                dias_diferencia += 7  # Es para la semana que viene

            fecha_objetivo = hoy + timedelta(days=dias_diferencia)

        # 3. Formateamos la fecha a YYYY-MM-DD
        fecha_YYYY_MM_DD = fecha_objetivo.strftime("%Y-%m-%d")

        # 4. Juntamos la fecha exacta con la hora que nos dio la IA
        inicio_final = f"{fecha_YYYY_MM_DD} {hora_inicio_HH_MM}:00"
        fin_final = f"{fecha_YYYY_MM_DD} {hora_fin_HH_MM}:00"

        # 5. Enviamos a tu Webhook correcto
        url = (
            "https://<N8N_PUBLIC_HOST>/webhook/<WEBHOOK_ID>"
        )

        payload = {
            "titulo": titulo,
            "descripcion": descripcion,
            "inicio": inicio_final,
            "fin": fin_final,
        }

        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                return f"✅ Evento '{titulo}' guardado en tu calendario para el {inicio_final}."
            else:
                return f"❌ Error de n8n. Código: {response.status_code}"
        except Exception as e:
            return f"❌ Error de red: {str(e)}"
