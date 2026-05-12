import requests
import json


class Tools:
    def __init__(self):
        self.webhook_url = (
            "https://<N8N_PUBLIC_HOST>/webhook/<WEBHOOK_ID>"
        )

    def manage_shopping_list(self, action: str, item: str = "") -> str:
        """
        Manages the shopping list (todo entity).
        Actions: 'add', 'delete', or 'read'.
        """
        action = action.lower().strip()
        item = item.strip()

        if action not in ["add", "delete", "read"]:
            return "Error: Use 'add', 'delete' or 'read'."

        try:
            response = requests.post(
                self.webhook_url, json={"action": action, "item": item}, timeout=15
            )

            if response.status_code == 200:
                if action == "read":
                    try:
                        data = response.json()
                        # Navegamos por la estructura: service_response -> todo.lista_de_la_compra -> items
                        # Usamos .get() para que no explote si algo falta
                        service_res = data.get("service_response", {})
                        entity_data = service_res.get("todo.lista_de_la_compra", {})
                        items_list = entity_data.get("items", [])

                        # Si n8n devolvió la lista directamente sin el "service_response"
                        if not items_list and isinstance(data, list):
                            items_list = data
                        elif not items_list and "items" in data:
                            items_list = data["items"]

                        # Sacamos el 'summary' de cada producto que no esté completado
                        active_items = [
                            i["summary"]
                            for i in items_list
                            if i.get("status") != "completed"
                        ]

                        if not active_items:
                            return "The list is empty, my lord. We are ready for the feast."

                        return "In your list: " + ", ".join(active_items)
                    except Exception as e:
                        return f"I can see the data, but I cannot read it. n8n sent: {str(data)[:100]}"

                return "Done."
            return f"n8n error {response.status_code}"
        except Exception as e:
            return f"The connection to Midgard failed: {str(e)}"
