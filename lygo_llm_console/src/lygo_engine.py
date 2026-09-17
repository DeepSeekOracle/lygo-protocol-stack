"""LYGO Engine — hybrid brain.

One planner, two runtimes:
- llama.cpp GGUF: mmap SSD + RAM + optional GPU layers (onboard)
- Colibri MoE: VRAM + RAM + SSD expert streaming (JustVugg/colibri)

Placement only changes speed. Semantics stay the model. RESOURCE backends; CANON unchanged.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from engine import available_ram_bytes, ram_ok, resolve_binary, runner_for, spawn_runner
from paths import COLIBRI_PORT, LLAMA_PORT

GIB = 1024**3


def cpu_threads() -> int:
    n = os.cpu_count() or 4
    return max(4, min(16, n - 1 if n > 4 else n))


def vram_free_bytes() -> int:
    nvsmi = shutil.which("nvidia-smi")
    if not nvsmi:
        return 0
    try:
        r = subprocess.run(
            [nvsmi, "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=4,
            creationflags=0x08000000 if os.name == "nt" else 0,
        )
        if r.returncode != 0:
            return 0
        total = 0
        for line in (r.stdout or "").splitlines():
            line = line.strip()
            if line.isdigit():
                total += int(line) * 1024 * 1024
        return total
    except Exception:
        return 0


def probe() -> dict[str, Any]:
    ram = available_ram_bytes()
    vram = vram_free_bytes()
    return {
        "ram_bytes": ram,
        "ram_gib": round(ram / GIB, 2) if ram else 0,
        "vram_bytes": vram,
        "vram_gib": round(vram / GIB, 2) if vram else 0,
        "threads": cpu_threads(),
        "llama_binary": bool(resolve_binary()),
        "ssd_stream": True,
    }


def _is_colibri(rec: dict[str, Any]) -> bool:
    return rec.get("engine") == "colibri" or rec.get("kind") == "colibri"


def _is_moe(rec: dict[str, Any]) -> bool:
    blob = " ".join(
        str(rec.get(k) or "")
        for k in ("architecture", "id", "path", "note")
    ).lower()
    return any(x in blob for x in ("moe", "mixtral", "deepseek", "qwen2moe", "glm", "kimi", "olmoe"))


def plan(rec: dict[str, Any]) -> dict[str, Any]:
    """VRAM / RAM / SSD placement. Does not silently change precision."""
    hw = probe()
    ram = int(hw["ram_bytes"] or 0)
    vram = int(hw["vram_bytes"] or 0)
    threads = int(hw["threads"])
    coli = _is_colibri(rec)
    backend = "colibri" if coli else "llama"
    ngl = 0
    if vram >= 4 * GIB:
        ngl = 99
    elif vram >= 2 * GIB:
        ngl = 20
    pin_gib = max(2, int((ram * 0.55) / GIB)) if ram else 8
    cuda_expert = "auto" if vram >= 4 * GIB else "0"
    return {
        "backend": backend,
        "signature": "Δ9Φ963-LYGO-ENGINE-HYBRID-v1",
        "reason": "colibri_moe_stream" if coli else "llama_mmap_ssd_gpu",
        "moe": _is_moe(rec) or coli,
        "tiers": {
            "vram_gib": hw["vram_gib"],
            "ram_gib": hw["ram_gib"],
            "ssd_mmap": True,
            "policy": "placement_changes_speed_not_weights",
        },
        "llama": {
            "ngl": ngl,
            "threads": threads,
            "mmap": True,
            "mlock": False,
            "flash_attn": vram >= 4 * GIB,
        },
        "colibri": {
            "pin_gib": pin_gib,
            "cuda_expert_gb": cuda_expert,
            "port": COLIBRI_PORT,
        },
        "port": COLIBRI_PORT if coli else LLAMA_PORT,
        "hardware": hw,
    }


def boot(rec: dict[str, Any], *, api_key: str, state: dict[str, Any]) -> str:
    """Spawn the planned backend. Returns brain status string."""
    from colibri import resolve_coli, spawn_colibri

    p = Path(rec.get("path") or "")
    pl = plan(rec)
    state["lygo_engine"] = pl
    if pl["backend"] == "colibri":
        if resolve_coli() is None:
            state["brain"] = "missing_colibri"
            state["error"] = "coli launcher missing — scripts/fetch_colibri.ps1"
            return "missing_colibri"
        port = COLIBRI_PORT
        with __import__("engine").ENGINE_LOCK:
            existing = runner_for(port)
            if existing and existing.gguf == str(p):
                state["brain"] = "ready"
                state["engine"] = "lygo-colibri"
                state["engine_port"] = port
                return "ready"
            extra = {
                "PIN_GB": str(pl["colibri"]["pin_gib"]),
                "CUDA_EXPERT_GB": str(pl["colibri"]["cuda_expert_gb"]),
            }
            spawn_colibri(
                port=port,
                model_dir=p,
                alias=str(rec.get("id") or p.name),
                api_key=api_key,
                extra_env=extra,
            )
        state["brain"] = "ready"
        state["engine"] = "lygo-colibri"
        state["engine_port"] = port
        state["error"] = None
        state["selected"] = rec.get("id")
        return "ready"

    if resolve_binary() is None:
        state["brain"] = "missing"
        return "missing"
    size = int(rec.get("bytes") or (p.stat().st_size if p.is_file() else 0))
    ram = int(pl["hardware"].get("ram_bytes") or 0)
    # mmap + SSD: do not require the whole GGUF to fit in RAM (Colibri lesson).
    if ram and ram < 2.5 * GIB:
        state["brain"] = "ram_refused"
        return "ram_refused"
    if size and size < ram * 0.45 and not ram_ok(size):
        # tiny host + small model still honor headroom
        if ram < 6 * GIB:
            state["brain"] = "ram_refused"
            return "ram_refused"
    port = LLAMA_PORT
    lp = pl["llama"]
    with __import__("engine").ENGINE_LOCK:
        existing = runner_for(port)
        if existing and existing.gguf == str(p):
            state["brain"] = "ready"
            state["engine"] = "lygo-llama"
            state["engine_port"] = port
            return "ready"
        mm = Path(rec["mmproj"]) if rec.get("mmproj") else None
        spawn_runner(
            port=port,
            gguf=p,
            kind=rec.get("kind") or "chat",
            mmproj=mm,
            ctx=int(rec.get("ctx") or 4096),
            ngl=int(rec.get("n_gpu_layers") or lp["ngl"]),
            alias=rec.get("id") or p.stem,
            api_key=api_key,
            threads=int(lp["threads"]),
            mmap=True,
            skip_ram_gate=True,
        )
    state["brain"] = "ready"
    state["engine"] = "lygo-llama"
    state["engine_port"] = port
    state["error"] = None
    state["selected"] = rec.get("id")
    return "ready"


def status() -> dict[str, Any]:
    from colibri import resolve_coli

    return {
        "ok": True,
        "name": "LYGO Engine",
        "hybrid": True,
        "probe": probe(),
        "llama": bool(resolve_binary()),
        "colibri": bool(resolve_coli()),
        "ports": {"llama": LLAMA_PORT, "colibri": COLIBRI_PORT, "portal": 9641},
    }
