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
import urllib.parse
import urllib.request
from html import escape as html_escape
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

DEFAULT_TELEGRAM_CONFIG_SOURCES = [
    "/home/k1k3/odin/scripts/telegram.env",
    "/home/k1k3/odin/scripts/cron_odin_ingesta.sh",
    "/home/k1k3/odin/scripts/backup_diario.sh",
]

ODIN_SYNC_LOG = Path("/home/k1k3/odin_sync.log")
CRON_ODIN_LOG = Path("/home/k1k3/cron_odin.log")
STATE_FILE = Path("/home/k1k3/odin/logs/autorepair/state.json")


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


def tail_lines(path: Path, limit: int = 220) -> list[str]:
    try:
        lines = path.read_text(errors="ignore").splitlines()
    except FileNotFoundError:
        return []
    return lines[-limit:]


def check_ingestion_logs() -> dict[str, Any]:
    lines = tail_lines(ODIN_SYNC_LOG, 260)
    cron_lines = tail_lines(CRON_ODIN_LOG, 120)
    combined = lines + cron_lines

    missing_paths = sorted(set(re.findall(r"(?:can't open file '([^']+)'|(/home/k1k3/[^: ]+): not found)", "\n".join(combined))))
    flattened_missing = []
    for item in missing_paths:
        if isinstance(item, tuple):
            flattened_missing.extend([x for x in item if x])
        elif item:
            flattened_missing.append(item)

    processed = []
    for line in combined:
        for pattern in [r"Procesando:\s*(.+)$", r"Sincronizado:\s*(.+?)(?:\s*\(|$)"]:
            match = re.search(pattern, line)
            if match:
                processed.append(match.group(1).strip())

    detected = []
    for line in combined:
        if any(marker in line for marker in ["Sin cambios", "Todo está al día", "Procesando", "Sincronizado", "Detectados"]):
            detected.append(line.strip())

    return {
        "log_sources": [str(ODIN_SYNC_LOG), str(CRON_ODIN_LOG)],
        "recent_missing_paths_in_logs": sorted(set(flattened_missing)),
        "processed_sources": sorted(set(processed))[-30:],
        "recent_relevant_lines": detected[-30:],
    }


def check_cron_paths() -> dict[str, Any]:
    crontab = run(["crontab", "-l"], timeout=10)
    paths = []
    for line in crontab["stdout"].splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        paths.extend(re.findall(r"(/home/k1k3/[^\s]+)", line))
    missing = sorted({p for p in paths if not Path(p).exists()})
    return {
        "raw": crontab["stdout"],
        "referenced_paths": sorted(set(paths)),
        "missing_paths": missing,
    }


def check_qdrant() -> dict[str, Any]:
    # Qdrant HTTP API is enough here; no Python client dependency required.
    url = "http://127.0.0.1:6333/collections/memoria_ia"
    try:
        with urllib.request.urlopen(url, timeout=4) as response:
            data = json.loads(response.read().decode("utf-8"))
        result = data.get("result", {})
        return {
            "available": True,
            "collection": "memoria_ia",
            "status": result.get("status"),
            "vectors_count": result.get("vectors_count"),
            "points_count": result.get("points_count"),
            "indexed_vectors_count": result.get("indexed_vectors_count"),
        }
    except Exception as exc:
        return {"available": False, "collection": "memoria_ia", "error": str(exc)}


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


def load_state(path: Path = STATE_FILE) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def save_state(state: dict[str, Any], path: Path = STATE_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n")


def report_findings(report: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    ollama = report["checks"]["ollama"]
    if not ollama["service_active"]:
        findings.append({"severity": "critical", "title": "Ollama caído", "detail": "ollama.service no está activo."})
    elif not ollama["api_ok"]:
        findings.append({"severity": "critical", "title": "API de Ollama no responde", "detail": "La API local /api/tags no responde."})

    signals = ollama["signals"]
    if signals["runner_killed"]:
        findings.append({
            "severity": "warning",
            "title": "Runners de Ollama terminados",
            "detail": f"{signals['runner_killed']} eventos 'signal: killed' en las últimas 24h.",
        })
    if signals["amdgpu_queue_evicted"]:
        findings.append({
            "severity": "warning",
            "title": "Eventos AMDGPU",
            "detail": f"{signals['amdgpu_queue_evicted']} evacuaciones de cola AMDGPU en kernel.",
        })
    if signals["rocblaslt_missing_tensile"]:
        findings.append({
            "severity": "info",
            "title": "Avisos rocBLASLt/gfx1200",
            "detail": "Falta TensileLibrary_lazy_gfx1200.dat en logs de Ollama.",
        })
    if signals["prompt_truncated"]:
        findings.append({
            "severity": "info",
            "title": "Prompts truncados",
            "detail": f"{signals['prompt_truncated']} prompts superaron la ventana configurada.",
        })

    for container in report["checks"]["docker"].get("problem_containers", []):
        findings.append({
            "severity": "critical",
            "title": f"Contenedor problemático: {container['name']}",
            "detail": container["status"],
        })

    for warning in report["checks"]["disk"].get("warnings", []):
        findings.append({
            "severity": warning["severity"],
            "title": f"Disco {warning['mount']} al {warning['use_percent']}%",
            "detail": "Revisar limpieza, backups o traslado de datos.",
        })

    cron = report["checks"].get("cron", {})
    for path in cron.get("missing_paths", []):
        findings.append({
            "severity": "critical",
            "title": "Cron apunta a ruta inexistente",
            "detail": path,
        })

    ingestion = report["checks"].get("ingestion", {})
    if ingestion.get("recent_missing_paths_in_logs"):
        findings.append({
            "severity": "info",
            "title": "Hay errores antiguos/recientes de cron en logs",
            "detail": ", ".join(ingestion["recent_missing_paths_in_logs"][:4]),
        })

    qdrant = report["checks"].get("qdrant", {})
    if not qdrant.get("available"):
        findings.append({
            "severity": "warning",
            "title": "Qdrant/memoria_ia no comprobable",
            "detail": qdrant.get("error", "sin detalle"),
        })
    return findings


def finding_signature(findings: list[dict[str, str]]) -> str:
    relevant = [
        f"{f['severity']}|{f['title']}|{f['detail']}"
        for f in findings
        if f["severity"] in {"critical", "warning"}
    ]
    return "\n".join(sorted(relevant))


def load_telegram_config(paths: list[str]) -> tuple[str | None, str | None, str]:
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("CHAT_ID")
    source = "environment"
    if token and chat_id:
        return token, chat_id, source

    for path in paths:
        p = Path(path)
        if not p.exists():
            continue
        text = p.read_text(errors="ignore")
        token_match = re.search(r'(?m)^\s*(?:TOKEN|TELEGRAM_BOT_TOKEN)=["\']?([^"\'\n]+)', text)
        chat_match = re.search(r'(?m)^\s*(?:CHAT_ID|TELEGRAM_CHAT_ID)=["\']?([^"\'\n]+)', text)
        if token_match and chat_match:
            return token_match.group(1).strip(), chat_match.group(1).strip(), str(p)
    return None, None, "not_found"


def telegram_send(token: str, chat_id: str, message: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    chunks = [message[i:i + 3600] for i in range(0, len(message), 3600)]
    for chunk in chunks:
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            response.read()


def sev_icon(severity: str) -> str:
    return {
        "critical": "🔴",
        "warning": "🟠",
        "info": "🔵",
    }.get(severity, "⚪")


def short_line(text: str, limit: int = 145) -> str:
    clean = " ".join(str(text).split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1] + "…"


def format_telegram_report(report: dict[str, Any], daily: bool) -> str:
    findings = report.get("findings", [])
    critical = [f for f in findings if f["severity"] == "critical"]
    warnings = [f for f in findings if f["severity"] == "warning"]
    infos = [f for f in findings if f["severity"] == "info"]
    title = "📋 <b>Informe diario de Odín</b>" if daily else "⚠️ <b>Alerta de Odín</b>"
    health = "🟢 OK"
    if critical:
        health = "🔴 CRÍTICO"
    elif warnings:
        health = "🟠 ATENCIÓN"
    lines = [
        title,
        f"Estado general: <b>{health}</b>",
        f"Fecha UTC: <code>{html_escape(report['timestamp'])}</code>",
        f"Host: <code>{html_escape(report['hostname'])}</code>",
        "",
        "🧭 <b>Resumen</b>",
        f"🔴 Críticos: <b>{len(critical)}</b> · 🟠 Avisos: <b>{len(warnings)}</b> · 🔵 Info: <b>{len(infos)}</b>",
    ]

    ollama = report["checks"]["ollama"]
    gpu = report["checks"]["gpu"]
    disk = report["checks"]["disk"]
    docker = report["checks"]["docker"]
    qdrant = report["checks"].get("qdrant", {})
    ingestion = report["checks"].get("ingestion", {})
    cron = report["checks"].get("cron", {})

    lines += [
        "",
        "🫀 <b>Estado operativo</b>",
        f"• Ollama: servicio <b>{'OK' if ollama['service_active'] else 'KO'}</b>, API <b>{'OK' if ollama['api_ok'] else 'KO'}</b>",
        f"• GPU: uso <b>{gpu.get('gpu_use_percent')}%</b>, VRAM <b>{gpu.get('vram_allocated_percent')}%</b>, temp <code>{html_escape(str(gpu.get('temperatures_c')))}</code>",
        f"• Docker críticos problemáticos: <b>{len(docker.get('problem_containers', []))}</b>",
        f"• Cron rutas rotas actuales: <b>{len(cron.get('missing_paths', []))}</b>",
    ]
    disk_raw = disk.get("raw", "").splitlines()
    if len(disk_raw) > 1:
        lines.append("• Disco:")
        for row in disk_raw[1:]:
            lines.append(f"  <code>{html_escape(short_line(row, 115))}</code>")
    if qdrant:
        lines.append(
            f"• Qdrant <code>memoria_ia</code>: <b>{'OK' if qdrant.get('available') else 'KO'}</b>, puntos={qdrant.get('points_count')}, vectores={qdrant.get('vectors_count')}"
        )

    if findings:
        lines += ["", "🧯 <b>Qué hay de malo</b>"]
        for item in findings[:16]:
            icon = sev_icon(item["severity"])
            lines.append(
                f"{icon} <b>{html_escape(item['title'])}</b>\n"
                f"   <code>{html_escape(short_line(item['detail'], 155))}</code>"
            )
    else:
        lines += ["", "🧯 <b>Qué hay de malo</b>", "🟢 Nada crítico detectado."]

    recent = ingestion.get("recent_relevant_lines", [])
    processed = ingestion.get("processed_sources", [])
    lines += ["", "🆕 <b>Qué hay de nuevo</b>"]
    if recent:
        lines.extend(f"• {html_escape(short_line(line, 160))}" for line in recent[-10:])
    else:
        lines.append("• Sin actividad reciente detectada en logs de ingesta.")

    if processed:
        lines += ["", "🧠 <b>Fuentes de memoria procesadas recientemente</b>"]
        lines.extend(f"• <code>{html_escape(short_line(src, 150))}</code>" for src in processed[-12:])

    if report.get("actions"):
        lines += ["", "🛠️ <b>Acciones ejecutadas</b>"]
        for action in report["actions"]:
            rc = action.get("result", {}).get("returncode")
            lines.append(f"• <code>{html_escape(str(action.get('action')))}</code> rc={rc}")
    return "\n".join(lines)


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
    parser.add_argument("--telegram", action="store_true", help="send report to Telegram")
    parser.add_argument("--daily", action="store_true", help="send a complete daily report")
    parser.add_argument("--alert", action="store_true", help="send Telegram only when warning/critical state changes")
    parser.add_argument(
        "--telegram-config",
        action="append",
        default=[],
        help="file containing TOKEN/CHAT_ID or TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID",
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
            "ingestion": check_ingestion_logs(),
            "cron": check_cron_paths(),
            "qdrant": check_qdrant(),
        },
        "actions": [],
        "report_sources": [
            "systemctl status ollama",
            "journalctl -u ollama --since '24 hours ago'",
            "journalctl -k --since '24 hours ago'",
            "rocm-smi --showuse --showmemuse --showtemp --showpids",
            "docker ps -a",
            "df -h / /mnt/almacen",
            str(ODIN_SYNC_LOG),
            str(CRON_ODIN_LOG),
            "crontab -l",
            "http://127.0.0.1:6333/collections/memoria_ia",
        ],
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

    report["findings"] = report_findings(report)
    write_reports(report, Path(args.log_dir))

    if args.telegram or args.daily or args.alert:
        paths = args.telegram_config + DEFAULT_TELEGRAM_CONFIG_SOURCES
        token, chat_id, source = load_telegram_config(paths)
        report["telegram_config_source"] = source
        if not token or not chat_id:
            print("Telegram config not found", file=sys.stderr)
            return 2

        should_send = args.daily or args.telegram
        if args.alert:
            state = load_state()
            signature = finding_signature(report["findings"])
            should_send = bool(signature) and signature != state.get("last_alert_signature")
            if should_send:
                state["last_alert_signature"] = signature
                state["last_alert_at"] = report["timestamp"]
                save_state(state)

        if should_send:
            telegram_send(token, chat_id, format_telegram_report(report, daily=args.daily))

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
