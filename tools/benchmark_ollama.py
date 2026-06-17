#!/usr/bin/env python3
"""Benchmark reproducible de modelos Ollama mediante su API local."""

from __future__ import annotations

import argparse
import json
import time
import urllib.request


PROMPT = (
    "Responde en español con un máximo de 90 palabras. "
    "Contexto: la copia de infraestructura de Odín se ejecuta a las 04:00, "
    "conserva tres días en local y siete en el NVMe. "
    "Pregunta: ¿qué algoritmo de cifrado usa el NVMe? "
    "Si el contexto no lo indica, dilo explícitamente sin inventar."
)


def post_json(url: str, payload: dict, timeout: int = 900) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def get_json(url: str, timeout: int = 30) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)


def unload_all(base_url: str) -> None:
    for loaded in get_json(f"{base_url}/api/ps").get("models", []):
        post_json(
            f"{base_url}/api/generate",
            {"model": loaded["name"], "prompt": "", "keep_alive": 0},
        )
    time.sleep(1)


def seconds(value: int | float | None) -> float:
    return round((value or 0) / 1_000_000_000, 3)


def run(base_url: str, model: str, num_ctx: int) -> dict:
    unload_all(base_url)

    rows = []
    for phase in ("cold", "warm"):
        started = time.perf_counter()
        result = post_json(
            f"{base_url}/api/generate",
            {
                "model": model,
                "prompt": PROMPT,
                "stream": False,
                "think": False,
                "keep_alive": "5m",
                "options": {
                    "temperature": 0,
                    "num_ctx": num_ctx,
                    "num_predict": 120,
                },
            },
        )
        wall = time.perf_counter() - started
        eval_duration = result.get("eval_duration", 0)
        rows.append(
            {
                "phase": phase,
                "wall_s": round(wall, 3),
                "load_s": seconds(result.get("load_duration")),
                "prompt_s": seconds(result.get("prompt_eval_duration")),
                "generation_s": seconds(eval_duration),
                "tokens": result.get("eval_count", 0),
                "tokens_s": round(
                    result.get("eval_count", 0) / (eval_duration / 1e9), 2
                )
                if eval_duration
                else 0,
                "response": (
                    result.get("response") or result.get("thinking") or ""
                ).strip(),
            }
        )

    loaded = get_json(f"{base_url}/api/ps").get("models", [])
    resident = next((item for item in loaded if item["name"] == model), {})
    return {
        "model": model,
        "num_ctx": num_ctx,
        "size_vram_bytes": resident.get("size_vram"),
        "runs": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--num-ctx", type=int, default=4096)
    parser.add_argument("models", nargs="+")
    args = parser.parse_args()

    results = [run(args.base_url.rstrip("/"), model, args.num_ctx) for model in args.models]
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
