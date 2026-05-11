#!/usr/bin/env python3
"""Export a compact Odín health snapshot for Home Assistant."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path


OUTPUT = Path("/home/k1k3/odin/public/ha_status.json")
AUTOREPAIR_LATEST = Path("/home/k1k3/odin/logs/autorepair/autorepair-latest.json")

ENDPOINTS = {
    "open_webui": "http://127.0.0.1:3000/health",
    "immich": "http://127.0.0.1:2283/api/server/ping",
    "qdrant": "http://127.0.0.1:6333/collections/memoria_ia",
    "n8n": "http://127.0.0.1:5679/",
    "nextcloud": "http://127.0.0.1:8082/",
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
        with urllib.request.urlopen(ENDPOINTS["qdrant"], timeout=5) as response:
            payload = json.load(response)
        return payload.get("result", {}).get("points_count")
    except Exception:
        return None


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
    docker = docker_summary()
    autorepair = load_autorepair()
    root_used = disk_summary()["root"]["used_percent"]
    endpoint_failures = [name for name, status in endpoints.items() if status is None or status >= 500]

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
        "qdrant_points": qdrant_points(),
        "disk": disk_summary(),
        "autorepair": autorepair,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
