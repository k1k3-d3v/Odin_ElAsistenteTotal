#!/usr/bin/env python3
"""Export a compact Odín health snapshot for Home Assistant."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


OUTPUT = Path("/home/k1k3/odin/public/ha_status.json")
AUTOREPAIR_LATEST = Path("/home/k1k3/odin/logs/autorepair/autorepair-latest.json")
HOME_ASSISTANT_ENV = Path("/home/k1k3/odin/scripts/home_assistant.env")

ENDPOINTS = {
    "open_webui": "http://127.0.0.1:3000/health",
    "ollama": "http://127.0.0.1:11434/api/tags",
    "immich": "http://127.0.0.1:2283/api/server/ping",
    "qdrant": "http://127.0.0.1:6333/healthz",
    "n8n": "http://127.0.0.1:5679/healthz",
    "nextcloud": "http://127.0.0.1:8082/status.php",
    "netdata": "http://127.0.0.1:19999/api/v1/info",
    "mealie": "http://127.0.0.1:9925/api/app/about",
    "frigate": "http://127.0.0.1:5001/api/stats",
    "stirling_pdf": "http://127.0.0.1:8080/api/v1/info/status",
    "crawl4ai": "http://127.0.0.1:11235/health",
    "evolution_api": "http://127.0.0.1:8085/",
    "pockettts": "http://127.0.0.1:49112/health",
    "faster_whisper": "http://127.0.0.1:10301/health",
}

TCP_ENDPOINTS = {
    "piper": ("127.0.0.1", 10200),
    "wyoming_whisper": ("127.0.0.1", 10300),
    "odin_asr": ("127.0.0.1", 5002),
}

SERVICE_METADATA = {
    "open_webui": ("Open WebUI", "mdi:chat-processing", "http://192.168.1.133:3000"),
    "ollama": ("Ollama", "mdi:brain", "http://192.168.1.133:11434"),
    "immich": ("Immich", "mdi:image-multiple", "http://192.168.1.133:2283"),
    "qdrant": ("Qdrant", "mdi:database-search", "http://192.168.1.133:6333/dashboard"),
    "n8n": ("n8n", "mdi:transit-connection-variant", "http://192.168.1.133:5679"),
    "nextcloud": ("Nextcloud", "mdi:cloud", "http://192.168.1.133:8082"),
    "netdata": ("Netdata", "mdi:chart-areaspline", "http://192.168.1.133:19999"),
    "mealie": ("Mealie", "mdi:food-apple", "http://192.168.1.133:9925"),
    "frigate": ("Frigate", "mdi:cctv", "http://192.168.1.133:5001"),
    "stirling_pdf": ("Stirling PDF", "mdi:file-pdf-box", "http://192.168.1.133:8080"),
    "crawl4ai": ("Crawl4AI", "mdi:web", "http://192.168.1.133:11235"),
    "evolution_api": ("Evolution API", "mdi:message-processing", "http://192.168.1.133:8085"),
    "pockettts": ("PocketTTS", "mdi:account-voice", "http://192.168.1.133:49112"),
    "faster_whisper": ("Faster Whisper", "mdi:microphone-message", "http://192.168.1.133:10301"),
    "piper": ("Piper", "mdi:account-voice", "tcp://192.168.1.133:10200"),
    "wyoming_whisper": ("Wyoming Whisper", "mdi:microphone", "tcp://192.168.1.133:10300"),
    "odin_asr": ("Odín ASR", "mdi:waveform", "http://192.168.1.133:5002"),
}


def run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, (proc.stdout + proc.stderr).strip()
    except Exception as exc:  # pragma: no cover - defensive runtime exporter
        return 1, str(exc)


def http_status(url: str, timeout: int = 5) -> int | None:
    try:
        request = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.getcode()
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:
        return None


def tcp_status(host: str, port: int, timeout: int = 3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def docker_summary() -> dict:
    code, output = run(
        [
            "docker",
            "ps",
            "-a",
            "--format",
            "{{.Names}}|{{.Status}}|{{.Label \"com.docker.compose.project\"}}",
        ]
    )
    containers = []
    unlabeled = []
    unhealthy = []

    if code == 0 and output:
        for line in output.splitlines():
            parts = line.split("|", 2)
            if len(parts) != 3:
                continue
            name, status, project = parts
            containers.append({"name": name, "status": status, "project": project})
            if not project:
                unlabeled.append(name)
            if "unhealthy" in status.lower() or "exited" in status.lower() or "restarting" in status.lower():
                unhealthy.append(name)

    compose_code, compose_output = run(["docker", "compose", "ls", "--format", "json"])
    compose_projects = []
    if compose_code == 0 and compose_output:
        try:
            parsed = json.loads(compose_output)
            if isinstance(parsed, list):
                compose_projects = parsed
            elif isinstance(parsed, dict):
                compose_projects = [parsed]
        except json.JSONDecodeError:
            for line in compose_output.splitlines():
                try:
                    item = json.loads(line)
                    if isinstance(item, dict):
                        compose_projects.append(item)
                except json.JSONDecodeError:
                    pass

    return {
        "containers_total": len(containers),
        "containers_unlabeled": len(unlabeled),
        "containers_unhealthy": len(unhealthy),
        "unlabeled": unlabeled,
        "unhealthy": unhealthy,
        "compose_projects": [p.get("Name") for p in compose_projects if p.get("Name")],
    }


def disk_summary() -> dict:
    result = {}
    for name, path in {"root": "/", "almacen": "/mnt/almacen"}.items():
        usage = shutil.disk_usage(path)
        result[name] = {
            "total_gb": round(usage.total / 1024**3, 1),
            "used_gb": round(usage.used / 1024**3, 1),
            "free_gb": round(usage.free / 1024**3, 1),
            "used_percent": round((usage.used / usage.total) * 100, 1),
        }
    return result


def qdrant_points() -> int | None:
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1:6333/collections/memoria_ia", timeout=5
        ) as response:
            payload = json.load(response)
        return payload.get("result", {}).get("points_count")
    except Exception:
        return None


def load_env(path: Path) -> dict[str, str]:
    values = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def get_ha_state(ha_url: str, token: str, entity_id: str) -> dict | None:
    try:
        request = urllib.request.Request(
            f"{ha_url.rstrip('/')}/api/states/{entity_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def post_ha_state(
    ha_url: str,
    token: str,
    entity_id: str,
    state: str | int | float,
    attributes: dict,
) -> None:
    request = urllib.request.Request(
        f"{ha_url.rstrip('/')}/api/states/{entity_id}",
        data=json.dumps({"state": state, "attributes": attributes}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=8):
        pass


def publish_to_home_assistant(payload: dict) -> None:
    config = load_env(HOME_ASSISTANT_ENV)
    ha_url = config.get("HA_URL")
    token = config.get("HA_TOKEN")
    if not ha_url or not token:
        return

    common = {"updated_at": payload["generated_at"]}
    docker = payload["docker"]
    disk = payload["disk"]
    autorepair = payload["autorepair"]

    # Fetch real energy metrics from Home Assistant
    torre_power = get_ha_state(ha_url, token, "sensor.servidor_torre_power")
    torre_day = get_ha_state(ha_url, token, "sensor.servidor_torre_energy_day")
    torre_month = get_ha_state(ha_url, token, "sensor.servidor_torre_energy_month")

    rpi5_power = get_ha_state(ha_url, token, "sensor.servidor_rpi5_power")
    rpi5_day = get_ha_state(ha_url, token, "sensor.servidor_rpi5_energy_day")
    rpi5_month = get_ha_state(ha_url, token, "sensor.servidor_rpi5_energy_month")

    def to_float(val_dict: dict | None, default: float = 0.0) -> float:
        if not val_dict:
            return default
        try:
            return float(val_dict.get("state", default))
        except (ValueError, TypeError):
            return default

    states = {
        "sensor.odin_estado": (
            payload["overall"],
            {
                **common,
                "friendly_name": "Odín Estado",
                "icon": "mdi:server-network",
                "findings": autorepair.get("findings", []),
            },
        ),
        "sensor.odin_contenedores": (
            docker["containers_total"],
            {
                **common,
                "friendly_name": "Odín Contenedores",
                "icon": "mdi:docker",
                "unit_of_measurement": "contenedores",
                "compose_projects": docker["compose_projects"],
            },
        ),
        "sensor.odin_contenedores_con_problemas": (
            docker["containers_unhealthy"],
            {
                **common,
                "friendly_name": "Odín Contenedores con problemas",
                "icon": "mdi:alert-circle",
                "unhealthy": docker["unhealthy"],
            },
        ),
        "sensor.odin_qdrant_puntos": (
            payload.get("qdrant_points") or 0,
            {
                **common,
                "friendly_name": "Odín Memoria Qdrant",
                "icon": "mdi:database-search",
                "unit_of_measurement": "puntos",
            },
        ),
        "sensor.odin_disco_raiz": (
            disk["root"]["used_percent"],
            {
                **common,
                **disk["root"],
                "friendly_name": "Odín Disco raíz",
                "icon": "mdi:harddisk",
                "unit_of_measurement": "%",
            },
        ),
        "sensor.odin_disco_almacen": (
            disk["almacen"]["used_percent"],
            {
                **common,
                **disk["almacen"],
                "friendly_name": "Odín Disco almacén",
                "icon": "mdi:database",
                "unit_of_measurement": "%",
            },
        ),
        "sensor.odin_avisos": (
            autorepair.get("warning_count", 0) + autorepair.get("critical_count", 0),
            {
                **common,
                "friendly_name": "Odín Avisos",
                "icon": "mdi:alert",
                "warnings": autorepair.get("warning_count", 0),
                "critical": autorepair.get("critical_count", 0),
                "findings": autorepair.get("findings", []),
            },
        ),
        "sensor.odin_consumo_servidor": (
            to_float(torre_power, 0.0),
            {
                **common,
                "friendly_name": "Odín Consumo servidor",
                "icon": "mdi:power-plug",
                "unit_of_measurement": "W",
                "device_class": "power",
                "power_w": to_float(torre_power, 0.0),
                "energy_day_kwh": to_float(torre_day, 0.0),
                "energy_month_kwh": to_float(torre_month, 0.0),
                "description": "Potencia y energía consumida por la torre del servidor.",
            },
        ),
        "sensor.odin_consumo_auxiliar": (
            to_float(rpi5_power, 0.0),
            {
                **common,
                "friendly_name": "Odín Consumo auxiliar",
                "icon": "mdi:power-socket-eu",
                "unit_of_measurement": "W",
                "device_class": "power",
                "power_w": to_float(rpi5_power, 0.0),
                "energy_day_kwh": to_float(rpi5_day, 0.0),
                "energy_month_kwh": to_float(rpi5_month, 0.0),
                "description": "Potencia y energía consumida por la Raspberry Pi 5 y periféricos de red.",
            },
        ),
        "sensor.odin_backup_estado": (
            "pendiente",
            {
                **common,
                "friendly_name": "Odín Backup NVMe",
                "icon": "mdi:backup-restore",
                "description": "NVMe disponible; montaje y primera copia pendientes.",
            },
        ),
        "sensor.odin_backup_ultima_copia": (
            "sin copia",
            {
                **common,
                "friendly_name": "Odín Último backup",
                "icon": "mdi:calendar-clock",
            },
        ),
        "sensor.odin_backup_tamano": (
            0,
            {
                **common,
                "friendly_name": "Odín Tamaño del backup",
                "icon": "mdi:harddisk-plus",
                "unit_of_measurement": "GB",
            },
        ),
    }

    for entity_id, (state, attributes) in states.items():
        post_ha_state(ha_url, token, entity_id, state, attributes)

    for service, available in payload["services"].items():
        name, icon, service_url = SERVICE_METADATA[service]
        post_ha_state(
            ha_url,
            token,
            f"binary_sensor.odin_{service}",
            "on" if available else "off",
            {
                **common,
                "friendly_name": name,
                "device_class": "connectivity",
                "icon": icon,
                "service_url": service_url,
            },
        )


def load_autorepair() -> dict:
    if not AUTOREPAIR_LATEST.exists():
        return {}
    try:
        with AUTOREPAIR_LATEST.open() as handle:
            data = json.load(handle)
    except Exception:
        return {}
    findings = data.get("findings", [])
    return {
        "timestamp": data.get("timestamp"),
        "findings_count": len(findings),
        "critical_count": sum(1 for item in findings if item.get("severity") == "critical"),
        "warning_count": sum(1 for item in findings if item.get("severity") == "warning"),
        "findings": findings[:8],
    }


def main() -> int:
    endpoints = {name: http_status(url) for name, url in ENDPOINTS.items()}
    tcp_endpoints = {
        name: tcp_status(host, port) for name, (host, port) in TCP_ENDPOINTS.items()
    }
    services = {
        **{
            name: status is not None and status < 500
            for name, status in endpoints.items()
        },
        **tcp_endpoints,
    }
    docker = docker_summary()
    autorepair = load_autorepair()
    root_used = disk_summary()["root"]["used_percent"]
    endpoint_failures = [name for name, available in services.items() if not available]

    overall = "ok"
    if docker["containers_unhealthy"] or docker["containers_unlabeled"] or endpoint_failures:
        overall = "warning"
    if autorepair.get("critical_count", 0) > 0 or root_used >= 90:
        overall = "critical"

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "host": "odin",
        "overall": overall,
        "docker": docker,
        "endpoints": endpoints,
        "tcp_endpoints": tcp_endpoints,
        "services": services,
        "qdrant_points": qdrant_points(),
        "disk": disk_summary(),
        "autorepair": autorepair,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(OUTPUT)
    try:
        publish_to_home_assistant(payload)
    except Exception as exc:
        print(f"Warning: no se pudieron publicar estados en Home Assistant: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
