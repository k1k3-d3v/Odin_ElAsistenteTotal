#!/usr/bin/env python3
"""Odín self-repair helper.

This script is intentionally conservative. By default it diagnoses and writes a
report. With --repair it only performs low-risk actions, currently starting
Ollama when the service is inactive. Restarting a running service requires the
explicit --restart-ollama flag.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


IMPORTANT_CONTAINERS = {
    "n8n-odin",
    "webui-odin",
    "qdrant-odin",
    "nextcloud-odin",
    "immich_server",
    "immich_machine_learning",
    "frigate",
    "piper",
    "odin-asr",
    "wyoming-whisper",
    "faster-whisper-server",
    "crawl4ai",
}


def run(cmd: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except FileNotFoundError:
        return {"cmd": cmd, "returncode": 127, "stdout": "", "stderr": "command not found"}
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": cmd,
            "returncode": 124,
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": f"timeout after {timeout}s",
        }


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def check_ollama() -> dict[str, Any]:
    service = run(["systemctl", "is-active", "ollama"], timeout=10)
    api = run(["curl", "-fsS", "--max-time", "3", "http://127.0.0.1:11434/api/tags"], timeout=5)
    status = run(["systemctl", "status", "ollama", "--no-pager", "-l"], timeout=10)
    logs = run(
        ["journalctl", "-u", "ollama", "--since", "24 hours ago", "--no-pager", "-n", "260"],
        timeout=15,
    )

    text = logs["stdout"] + "\n" + logs["stderr"]
    signals = {
        "runner_killed": text.count('llama runner terminated" error="signal: killed"'),
        "rocblaslt_missing_tensile": text.count("TensileLibrary_lazy_gfx1200.dat"),
        "prompt_truncated": text.count("truncating input prompt"),
        "http_500": len(re.findall(r"\|\s+500\s+\|", text)),
        "manual_or_clean_stop": int("Stopping ollama.service" in text or "Deactivated successfully" in text),
        "amdgpu_queue_evicted": 0,
    }

    kernel = run(
        ["journalctl", "-k", "--since", "24 hours ago", "--no-pager"],
        timeout=15,
    )
    kernel_text = kernel["stdout"] + "\n" + kernel["stderr"]
    signals["amdgpu_queue_evicted"] = kernel_text.count("amdgpu: Freeing queue vital buffer")

    causes: list[str] = []
    if service["stdout"] != "active":
        causes.append("ollama_service_inactive")
    if api["returncode"] != 0:
        causes.append("ollama_api_unreachable")
    if signals["runner_killed"]:
        causes.append("llama_runner_killed")
    if signals["amdgpu_queue_evicted"]:
        causes.append("amdgpu_queue_evictions")
    if signals["rocblaslt_missing_tensile"]:
        causes.append("rocblaslt_missing_tensile_library_for_gfx1200")
    if signals["http_500"]:
        causes.append("ollama_http_500_responses")
    if signals["prompt_truncated"]:
        causes.append("prompts_exceed_context_window")

    return {
        "service_active": service["stdout"] == "active",
        "api_ok": api["returncode"] == 0,
        "status_excerpt": "\n".join(status["stdout"].splitlines()[:18]),
        "signals": signals,
        "likely_causes": causes,
    }


def check_gpu() -> dict[str, Any]:
    if not command_exists("rocm-smi"):
        return {"available": False, "error": "rocm-smi not found"}
    smi = run(["rocm-smi", "--showuse", "--showmemuse", "--showtemp", "--showpids"], timeout=15)
    text = smi["stdout"]
    gpu_use = re.search(r"GPU use \(%\):\s+(\d+)", text)
    vram = re.search(r"GPU Memory Allocated \(VRAM%\):\s+(\d+)", text)
    temps = re.findall(r"Temperature .*?\(C\):\s+([0-9.]+)", text)
    return {
        "available": smi["returncode"] == 0,
        "gpu_use_percent": int(gpu_use.group(1)) if gpu_use else None,
        "vram_allocated_percent": int(vram.group(1)) if vram else None,
        "temperatures_c": [float(t) for t in temps],
        "raw_excerpt": "\n".join(text.splitlines()[:80]),
    }


def check_docker() -> dict[str, Any]:
    if not command_exists("docker"):
        return {"available": False, "error": "docker not found"}
    ps = run(
        [
            "docker",
            "ps",
            "-a",
            "--format",
            "{{.Names}}\t{{.Status}}\t{{.Image}}",
        ],
        timeout=20,
    )
    containers = []
    problem_containers = []
    for line in ps["stdout"].splitlines():
        if not line.strip():
            continue
        name, status, image = (line.split("\t", 2) + ["", ""])[:3]
        item = {"name": name, "status": status, "image": image}
        containers.append(item)
        is_problem = "Exited" in status or "unhealthy" in status.lower() or "Restarting" in status
        if name in IMPORTANT_CONTAINERS and is_problem:
            problem_containers.append(item)
    return {
        "available": ps["returncode"] == 0,
        "problem_containers": problem_containers,
        "important_running": [
            c for c in containers if c["name"] in IMPORTANT_CONTAINERS and c not in problem_containers
        ],
    }


def check_disk() -> dict[str, Any]:
    df = run(["df", "-P", "-h", "/", "/mnt/almacen"], timeout=10)
    warnings = []
    for line in df["stdout"].splitlines()[1:]:
        parts = line.split()
        if len(parts) < 6:
            continue
        use = parts[4].rstrip("%")
        try:
            use_int = int(use)
        except ValueError:
            continue
        if use_int >= 90:
            warnings.append({"mount": parts[5], "use_percent": use_int, "severity": "critical"})
        elif use_int >= 80:
            warnings.append({"mount": parts[5], "use_percent": use_int, "severity": "warning"})
    return {"raw": df["stdout"], "warnings": warnings}


def repair(report: dict[str, Any], restart_ollama: bool) -> list[dict[str, Any]]:
    actions = []
    ollama = report["checks"]["ollama"]
    if not ollama["service_active"]:
        actions.append({
            "action": "start_ollama",
            "result": run(["sudo", "-n", "systemctl", "start", "ollama"], timeout=20),
        })
    elif restart_ollama and not ollama["api_ok"]:
        actions.append({
            "action": "restart_ollama",
            "result": run(["sudo", "-n", "systemctl", "restart", "ollama"], timeout=30),
        })
    return actions


def write_reports(report: dict[str, Any], log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = report["timestamp"].replace(":", "").replace("-", "").replace("+", "Z")
    json_path = log_dir / f"autorepair-{stamp}.json"
    latest_path = log_dir / "autorepair-latest.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    latest_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose and safely repair Odín services.")
    parser.add_argument("--repair", action="store_true", help="perform safe repair actions")
    parser.add_argument(
        "--restart-ollama",
        action="store_true",
        help="allow restarting Ollama if the service is active but the API is down",
    )
    parser.add_argument(
        "--log-dir",
        default="/home/k1k3/odin/logs/autorepair",
        help="directory where JSON reports are written",
    )
    args = parser.parse_args()

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hostname": run(["hostname"], timeout=5)["stdout"],
        "mode": "repair" if args.repair else "diagnose",
        "checks": {
            "ollama": check_ollama(),
            "gpu": check_gpu(),
            "docker": check_docker(),
            "disk": check_disk(),
        },
        "actions": [],
        "notes": [
            "No containers are restarted automatically.",
            "Ollama is only started automatically when inactive and --repair is used.",
            "Restarting an active Ollama service requires --restart-ollama.",
        ],
    }

    if args.repair:
        report["actions"] = repair(report, restart_ollama=args.restart_ollama)
        # Re-check Ollama after repair attempts.
        report["post_repair_ollama"] = check_ollama()

    write_reports(report, Path(args.log_dir))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
