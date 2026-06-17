#!/usr/bin/env python3
"""Create or update the Odín Lovelace dashboard through the HA WebSocket API."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import websocket


def load_env(path: Path) -> dict[str, str]:
    values = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


class HomeAssistantWebSocket:
    def __init__(self, url: str, token: str):
        self.ws = websocket.create_connection(url, timeout=15)
        self.message_id = 0
        required = json.loads(self.ws.recv())
        if required.get("type") != "auth_required":
            raise RuntimeError(f"Respuesta inesperada: {required}")
        self.ws.send(json.dumps({"type": "auth", "access_token": token}))
        auth = json.loads(self.ws.recv())
        if auth.get("type") != "auth_ok":
            raise RuntimeError(f"Autenticación rechazada: {auth}")

    def call(self, message_type: str, **payload):
        self.message_id += 1
        request = {"id": self.message_id, "type": message_type, **payload}
        self.ws.send(json.dumps(request))
        while True:
            response = json.loads(self.ws.recv())
            if response.get("id") != self.message_id:
                continue
            if not response.get("success"):
                raise RuntimeError(
                    f"{message_type}: {response.get('error', response)}"
                )
            return response.get("result")

    def close(self) -> None:
        self.ws.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("/home/k1k3/odin/dashboard/odin-dashboard.json"),
    )
    parser.add_argument(
        "--env",
        type=Path,
        default=Path("/home/k1k3/odin/scripts/home_assistant.env"),
    )
    args = parser.parse_args()

    env = {**load_env(args.env), **os.environ}
    ha_url = env["HA_URL"].rstrip("/")
    token = env["HA_TOKEN"]
    ws_url = ha_url.replace("http://", "ws://").replace("https://", "wss://")
    client = HomeAssistantWebSocket(f"{ws_url}/api/websocket", token)

    try:
        dashboards = client.call("lovelace/dashboards/list") or []
        dashboard_path = "odin-panel"
        existing = next(
            (item for item in dashboards if item.get("url_path") == dashboard_path),
            None,
        )
        if existing is None:
            client.call(
                "lovelace/dashboards/create",
                url_path=dashboard_path,
                title="Odín",
                icon="mdi:server-network",
                show_in_sidebar=True,
                require_admin=False,
            )
        else:
            client.call(
                "lovelace/dashboards/update",
                dashboard_id=existing["id"],
                title="Odín",
                icon="mdi:server-network",
                show_in_sidebar=True,
                require_admin=False,
            )

        config = json.loads(args.config.read_text(encoding="utf-8"))
        client.call("lovelace/config/save", url_path=dashboard_path, config=config)
        saved = client.call("lovelace/config", url_path=dashboard_path)
        print(
            f"Dashboard Odín instalado: {len(saved.get('views', []))} vistas, "
            f"{sum(len(v.get('sections', [])) for v in saved.get('views', []))} secciones."
        )
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
