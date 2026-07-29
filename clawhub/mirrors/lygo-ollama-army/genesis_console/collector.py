#!/usr/bin/env python3
"""Genesis status collector — local Ollama + army workspace only (v0.7.0).

No GitHub/HF API, no drive-letter scan, no Discord/crypto integration imports.
Optional stack lattice verify only when LYGO_STACK_ROOT is set and valid.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL = ROOT.parent
sys.path.insert(0, str(SKILL))
from _safe_invoke import run_python, git_status_summary  # noqa: E402
from lygo_stack_root import resolve_stack_root_or_none  # noqa: E402

DATA_DIR = ROOT / "data"
STATUS_PATH = DATA_DIR / "status.json"
ARMY = SKILL
CC = ARMY / "ollama_command_center"
GENESIS_PORT = int(os.environ.get("LYGO_GENESIS_PORT", "9963"))


def probe_ollama() -> dict:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3) as resp:
            data = json.loads(resp.read().decode())
        models = [m.get("name") for m in data.get("models", [])]
        return {"ok": bool(models), "models": models[:12], "host": "127.0.0.1:11434"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:160]}


def army_queue() -> dict:
    tasks = CC / "tasks"
    results = CC / "results"
    nt = len(list(tasks.glob("*.task.json"))) if tasks.is_dir() else 0
    nr = len(list(results.glob("*.result.json"))) if results.is_dir() else 0
    return {"queued": nt, "results": nr}


def sentinel_status() -> dict:
    p = CC / "workspace" / "sentinel_status.json"
    if not p.is_file():
        return {"ok": False, "detail": "no sentinel_status.json yet"}
    try:
        return {"ok": True, "status": json.loads(p.read_text(encoding="utf-8"))}
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": str(exc)[:160]}


def optional_stack_lattice() -> dict:
    stack = resolve_stack_root_or_none(CC / "config" / "army_config.json")
    if not stack:
        return {"ok": True, "detail": "LYGO_STACK_ROOT unset — stack probe skipped"}
    script = stack / "tools" / "verify_lattice_alignment.py"
    if not script.is_file():
        return {"ok": False, "detail": "verify_lattice_alignment.py missing"}
    cp = run_python(script, cwd=stack, timeout=180, stack_root=stack)
    aligned = cp.returncode == 0 and "ALIGNED" in (cp.stdout or "")
    return {
        "ok": aligned,
        "summary": "ALIGNED" if aligned else "NEEDS_FIX",
        "exit_code": cp.returncode,
        "stack": str(stack),
        "git": git_status_summary(stack),
    }


def collect() -> dict:
    return {
        "signature": "Delta9Phi963-GENESIS-LOCAL-v0.7.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scope": "local_ollama_army_only",
        "links": {
            "genesis_local": f"http://127.0.0.1:{GENESIS_PORT}/",
            "ollama_local": "http://127.0.0.1:11434/",
        },
        "ollama": probe_ollama(),
        "army_queue": army_queue(),
        "sentinel": sentinel_status(),
        "stack_lattice": optional_stack_lattice(),
    }


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    blob = collect()
    STATUS_PATH.write_text(json.dumps(blob, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "path": str(STATUS_PATH), "ollama": blob["ollama"].get("ok")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
