#!/usr/bin/env python3
"""Read-only army health probes (v0.7.0). Does not prune queue or enqueue tasks unless --smoke."""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CC = HERE.parent
ARMY = CC.parent
_SKILL = ARMY
if str(_SKILL) not in sys.path:
    sys.path.insert(0, str(_SKILL))
from _safe_invoke import run_python  # noqa: E402

sys.path.insert(0, str(HERE))
from army_queue_utils import probe_http_ok, probe_tcp_port, queue_dirs, unique_task_count  # noqa: E402

OUT = CC / "workspace" / "army_health_last_run.json"


def probe_ollama() -> dict:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as resp:
            data = json.loads(resp.read().decode())
        models = [m.get("name") for m in data.get("models", [])]
        return {"ok": bool(models), "models": models[:12]}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:160]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="Optional: run sentinel once (still no queue prune)")
    ap.add_argument("--write", action="store_true", help="Write report JSON under workspace/")
    args = ap.parse_args()

    dirs = queue_dirs(CC, ARMY)
    report = {
        "signature": "Delta9Phi963-ARMY-HEALTH-READONLY-v0.7.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "ollama": probe_ollama(),
        "queue_unique": unique_task_count(dirs),
        "gateway_18789": {
            "listening": probe_tcp_port("127.0.0.1", 18789),
            "http_ok": probe_http_ok("http://127.0.0.1:18789/"),
        },
    }
    status = CC / "workspace" / "sentinel_status.json"
    if status.is_file():
        try:
            report["sentinel_cached"] = json.loads(status.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass

    if args.smoke:
        cp = run_python(HERE / "sentinel_heartbeat.py", timeout=240)
        report["sentinel_smoke_exit"] = cp.returncode

    print(json.dumps(report, indent=2))
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["ollama"].get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
