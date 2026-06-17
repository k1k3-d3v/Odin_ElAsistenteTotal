# Capturas pendientes para la memoria final

## Estado de incorporación

Capturas incorporadas a la memoria el 11 de junio de 2026:

- Tools de Open WebUI.
- Búsqueda visual en Immich.
- Consulta de Frigate desde el chat.
- Vistas Resumen, Servicios, Casa, Salud, Organización y Monitor.
- Historial de consumo de la torre y la Raspberry Pi.
- Dashboard en móvil y validación desde la barra lateral.
- Netdata, alerta proactiva de Telegram y consulta de memoria privada.
- Captura adicional de la biblioteca de recetas de Mealie.

No queda ninguna captura imprescindible pendiente para compilar y entregar la
memoria. La segunda captura de Casa no se ha incorporado porque mostraba
una dirección geocodificada exacta; se utilizó en su lugar la vista equivalente
sin ubicación personal.

## Criterios comunes

- Formato preferido: PNG.
- Resolución recomendada: 1600 px de ancho o superior.
- Usar el tema oscuro cuando sea la interfaz habitual del proyecto.
- Capturar únicamente la ventana o panel relevante, sin escritorio alrededor.
- Ocultar contraseñas, tokens, correos, IP públicas, claves API y ubicaciones exactas.
- Mantener visibles nombres de servicios, estados, métricas y fechas cuando sean evidencia.
- No fotografiar la pantalla con otro dispositivo: usar captura digital.

## Infraestructura e integraciones

### 02. Tools de Open WebUI

- Archivo: `figures/evidence/02-openwebui-tools.png`
- Abrir: panel de administración o configuración del modelo Odín.
- Debe verse: listado de tools activas y sus nombres.
- Incluir: Home Assistant, Frigate, Nextcloud, Immich, Mealie, salud del sistema y extracción de contenido.
- Evitar: mostrar el código completo si contiene tokens o claves.

### 03. Búsqueda de una fotografía en Immich desde el chat

- Archivo: `figures/evidence/03-immich-chat.png`
- Abrir: una conversación nueva con Odín.
- Petición sugerida: buscar una fotografía reconocible pero no íntima.
- Debe verse: petición, llamada a la tool y fotografía renderizada dentro del chat.
- Ocultar: rostros de terceros si no se dispone de consentimiento.

### 04. Consulta de Frigate desde el chat

- Archivo: `figures/evidence/04-frigate-chat.png`
- Abrir: conversación con Odín.
- Petición sugerida: mostrar la última captura o el último evento de la cámara.
- Debe verse: petición, fuente/tool utilizada y JPEG renderizado.
- Evitar: imágenes de la vía pública, vecinos o información privada.

## Dashboard de Home Assistant

### 05. Vista Resumen

- Archivo: `figures/evidence/05-dashboard-resumen.png`
- Abrir: Odín, pestaña Resumen, en escritorio.
- Debe verse: cabecera completa, navegación, estado operativo, Salud ahora, tiempo, biblioteca y núcleo de inteligencia.
- Esperar a que todas las entidades hayan terminado de cargar.

### 06. Vista Servicios

- Archivo: `figures/evidence/06-dashboard-servicios.png`
- Abrir: pestaña Servicios.
- Debe verse: bloques de IA, automatización, datos, contenidos, voz, vigilancia y monitorización.
- Procurar que no haya estados `unknown` o `unavailable` evitables.

### 07. Vista Casa

- Archivo: `figures/evidence/07-dashboard-casa.png`
- Abrir: pestaña Casa.
- Debe verse: cámara Tapo, aspirador, mapa, televisión y móviles.
- La cámara puede mostrar una escena neutra o permanecer ocultada si contiene personas.
- Ocultar direcciones geocodificadas exactas antes de capturar.

### 08. Vista Salud

- Archivo: `figures/evidence/08-dashboard-salud.png`
- Abrir: pestaña Salud.
- Debe verse: corazón de Salud, pasos, sueño, pulso, oxígeno, peso y composición corporal.
- Puede mantenerse la información clínica porque pertenece al autor, pero no deben aparecer datos de terceros.

### 09. Vista Organización

- Archivo: `figures/evidence/09-dashboard-organizacion.png`
- Abrir: pestaña Organización.
- Debe verse: lista de la compra, tareas pendientes y calendario.
- Utilizar tareas de ejemplo no sensibles y evitar citas privadas.

### 10. Vista Monitor

- Archivo: `figures/evidence/10-dashboard-monitor.png`
- Abrir: pestaña Monitor.
- Debe verse: estado del servidor, servicios críticos, discos y acceso a Netdata.
- Intentar encuadrar la vista completa sin que las tarjetas queden cortadas.

### 11. Consumo Sonoff y backup

- Archivo: `figures/evidence/11-dashboard-consumo.png`
- Abrir: parte inferior de Monitor.
- Debe verse: coste estimado, tarjetas compactas de Torre y Raspberry Pi, gráfica de potencia y gráfica de energía.
- Mantener visible la tarifa usada.
- El backup NVMe ya funciona; si se actualiza esta captura opcional, mostrar última copia y tamaño.

### 12. Dashboard en móvil

- Archivo: `figures/evidence/12-dashboard-movil.png`
- Abrir: app móvil o navegador del teléfono.
- Capturar: vista Resumen en orientación vertical.
- Debe verse: cabecera adaptada, navegación y al menos dos bloques sin solapamientos.

## Validación y resultados

### 13. Dashboard visible en la barra lateral

- Archivo: `figures/evidence/13-dashboard-validacion.png`
- Abrir: Home Assistant con la barra lateral expandida y Odín seleccionado.
- Debe verse: entrada Odín en el menú y la vista Resumen cargada.
- Esta captura demuestra instalación y acceso, no solo diseño visual.

### 14. Monitor nativo y acceso a Netdata

- Archivo: `figures/evidence/14-monitor-netdata-acceso.png`
- Abrir: pestaña Monitor.
- Debe verse: métricas nativas y el botón para abrir Netdata.
- No es necesario abrir Netdata en esta captura.

### 15. Dashboard de Netdata

- Archivo: `figures/evidence/15-netdata.png`
- Abrir: Netdata directamente en la red local.
- Debe verse: CPU, memoria, disco, red y una ventana temporal con actividad.
- Evitar paneles vacíos; realizar la captura mientras el servidor tenga actividad normal.

### 16. Estado agregado de Odín en Home Assistant

- Archivo: `figures/evidence/16-estado-odin-ha.png`
- Abrir: tarjeta o panel donde aparezcan `sensor.odin_estado`, contenedores, avisos y servicios críticos.
- Debe verse: estado general y varias entidades derivadas del exportador.
- Puede reutilizarse un recorte limpio de Monitor si contiene toda esta evidencia.

### 17. Alerta proactiva

- Archivo: `figures/evidence/17-alerta-proactiva.png`
- Abrir: Telegram o notificación de Home Assistant.
- Debe verse: una alerta real de Odín con fecha, servicio afectado y mensaje comprensible.
- Ocultar: teléfono, nombre de usuario, identificadores de chat y contenido ajeno.

### 18. Consulta de memoria privada

- Archivo: `figures/evidence/18-consulta-memoria.png`
- Abrir: conversación con Odín.
- Pregunta sugerida: consultar un dato reconocible de una nota o documento de prueba.
- Debe verse: consulta, tool de Nextcloud o Qdrant, fuente recuperada y respuesta basada en ella.
- Usar un documento preparado para la memoria, sin datos privados innecesarios.

## Orden recomendado de entrega

1. Capturas 05 a 12, porque comparten el dashboard y pueden hacerse en una sesión.
2. Capturas 01, 02 y 15, relacionadas con administración.
3. Capturas 03, 04 y 18, relacionadas con conversaciones.
4. Capturas 13, 14, 16 y 17, relacionadas con validación.
