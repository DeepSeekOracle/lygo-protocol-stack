#!/usr/bin/env python3
"""
LYGO Ollama Heartbeats ONLY — sentinel pulse every 5 minutes (v0.8.0).

Runs ONLY sentinel_heartbeat.py. No genesis collector, no daemons, no extra modules.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

_SKILL = Path(__file__).resolve().parents[2]
if str(_SKILL) not in sys.path:
    sys.path.insert(0, str(_SKILL))
from _safe_invoke import run_python  # noqa: E402

HERE = Path(__file__).resolve().parent
SENTINEL = HERE / "sentinel_heartbeat.py"
INTERVAL = 300


def main() -> int:
    print("LYGO Heartbeats ONLY — sentinel_heartbeat every 5 min (nothing else; Ctrl+C to stop)")
    while True:
        try:
            run_python(SENTINEL, timeout=240)
        except Exception as exc:
            print(f"[heartbeat] {exc}")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Heartbeats stopped.")
        raise SystemExit(0)