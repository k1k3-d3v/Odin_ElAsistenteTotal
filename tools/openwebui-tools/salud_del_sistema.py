import requests
import json


class Tools:
    def __init__(self):
        # URL del webhook de n8n encargado de vigilar y reparar el servidor.
        self.webhook_url = "https://<N8N_PUBLIC_HOST>/webhook/<WEBHOOK_ID>"

    def manage_system_health(self, action: str, service_name: str = "") -> str:
        """
        NOMBRE DE LA HERRAMIENTA:
        manage_system_health.

        IDENTIDAD:
        Esta herramienta es el vigía del núcleo de Midgard.
        Sirve para consultar el estado del servidor, revisar recursos, detectar problemas
        y ejecutar tareas básicas de mantenimiento o reparación.

        CUÁNDO USAR ESTA HERRAMIENTA:
        Usa esta herramienta cuando Quique pregunte por el estado del servidor, el estado
        del sistema, la GPU, la CPU, la memoria, los procesos, los servicios, el rendimiento,
        errores del servidor, lentitud, temperatura, carga del sistema o mantenimiento.

        También debes usarla cuando Quique diga cosas como:
        cómo está el servidor.
        revisa el servidor.
        mira la GPU.
        mira la CPU.
        qué procesos hay.
        limpia el servidor.
        haz limpieza.
        reinicia un servicio.
        reinicia ollama.
        reinicia n8n.
        reinicia open webui.
        comprueba si algo va mal.
        revisa Midgard.
        estado del núcleo.
        vigila el sistema.

        QUÉ HACE:
        Envía una acción a un webhook de n8n que consulta o repara el servidor.
        La herramienta puede pedir informes de estado o ejecutar acciones de mantenimiento.

        REGLA CRÍTICA PARA EL MODELO:
        Antes de usar esta herramienta, lee a fondo esta descripción.
        No inventes métricas del servidor.
        No digas que la GPU, CPU, memoria o procesos están bien si esta herramienta no lo ha devuelto.
        No digas que has limpiado o reiniciado algo si no has usado esta herramienta.
        No inventes nombres de servicios.
        Usa solo las acciones permitidas.
        Si Quique pide reiniciar un servicio, debes pasar el nombre del servicio en service_name.
        Si Quique no especifica qué servicio reiniciar, no inventes uno. Pide el nombre del servicio o usa una acción de diagnóstico como general si la intención es revisar.

        ACCIONES DISPONIBLES:
        action igual a "gpu_status":
        Consulta el estado de la GPU.
        Úsalo cuando Quique pregunte por la GPU, VRAM, uso gráfico, CUDA, NVIDIA o carga de la gráfica.

        action igual a "cpu_status":
        Consulta el estado de la CPU.
        Úsalo cuando Quique pregunte por CPU, procesador, carga, temperatura o rendimiento general del procesador.

        action igual a "general":
        Consulta el estado general del sistema.
        Úsalo cuando Quique pregunte cómo está el servidor, si todo va bien, estado de Midgard, salud del sistema o revisión general.

        action igual a "processes":
        Consulta procesos activos.
        Úsalo cuando Quique pregunte qué procesos hay, qué está consumiendo recursos o qué se está ejecutando.

        action igual a "clean":
        Ejecuta una limpieza o mantenimiento básico del servidor.
        Úsalo cuando Quique pida limpiar el servidor, liberar recursos, hacer limpieza o mantenimiento.

        action igual a "restart":
        Reinicia un servicio concreto.
        Úsalo solo cuando Quique pida reiniciar un servicio específico.
        Debes rellenar service_name con el nombre del servicio indicado por Quique.

        PARÁMETROS:
        action:
        Debe ser exactamente una de estas acciones:
        gpu_status.
        cpu_status.
        general.
        processes.
        clean.
        restart.

        service_name:
        Nombre del servicio que se quiere reiniciar.
        Solo es necesario cuando action es "restart".
        Para el resto de acciones puede quedar vacío.

        EJEMPLOS DE USO:
        Quique dice: cómo está el servidor.
        Usa action "general" y service_name vacío.

        Quique dice: mira la GPU.
        Usa action "gpu_status" y service_name vacío.

        Quique dice: mira la CPU.
        Usa action "cpu_status" y service_name vacío.

        Quique dice: qué procesos están consumiendo recursos.
        Usa action "processes" y service_name vacío.

        Quique dice: limpia el servidor.
        Usa action "clean" y service_name vacío.

        Quique dice: reinicia ollama.
        Usa action "restart" y service_name "ollama".

        Quique dice: reinicia n8n.
        Usa action "restart" y service_name "n8n".

        CUÁNDO NO USAR ESTA HERRAMIENTA:
        No la uses para controlar luces, sensores, enchufes o clima.
        No la uses para lista de la compra.
        No la uses para calendario.
        No la uses para cámaras.
        No la uses para buscar fotos.
        No la uses para buscar notas.
        No la uses para guardar notas.

        RESPUESTA ESPERADA:
        Si la herramienta devuelve un informe, resume el informe para Quique con claridad.
        Si el resultado ya es claro, puedes mostrarlo directamente.
        Si hay error de conexión, informa de que no se ha podido conectar con el servidor.
        Si el webhook devuelve un código de error, informa del código sin inventar detalles.

        PRIORIDAD:
        Esta herramienta tiene prioridad para cualquier petición relacionada con la salud,
        mantenimiento o reparación del servidor.
        No debe confundirse con get_health_status, que sirve para la salud física de Quique.
        manage_system_health es para la salud del servidor.
        get_health_status es para la salud de Quique.
        """
        action = action.lower().strip()

        # Enviamos siempre una acción normalizada al webhook de n8n.
        # service_name solo se usa cuando action es "restart".
        payload = {"action": action, "service": service_name}

        try:
            # Usamos POST para enviar el JSON con la acción solicitada.
            response = requests.post(self.webhook_url, json=payload, timeout=30)

            if response.status_code == 200:
                return f"Informe del sistema: {response.text}"
            else:
                return f"Error en el núcleo del servidor. Código de estado {response.status_code}"

        except Exception as e:
            return f"El Bifrost está cerrado. No he podido conectar con el servidor: {str(e)}"
