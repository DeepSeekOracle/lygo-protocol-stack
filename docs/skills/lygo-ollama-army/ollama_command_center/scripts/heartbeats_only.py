#!/usr/bin/env python3
"""
LYGO Ollama Heartbeats ONLY — sentinel pulse every 5 minutes.
No LLM daemons, no Genesis collector, no monitoring UI.
Collector runs only if LYGO_GENESIS_COLLECT=1 (opt-in).
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path as _P

_SKILL = _P(__file__).resolve().parents[2]
if str(_SKILL) not in sys.path:
    sys.path.insert(0, str(_SKILL))
from _safe_invoke import run_python  # noqa: E402

HERE = _P(__file__).resolve().parent
SENTINEL = HERE / "sentinel_heartbeat.py"
GENESIS_COLLECTOR = HERE.parents[1] / "genesis_console" / "collector.py"
INTERVAL = 300


def main() -> int:
    collect = os.environ.get("LYGO_GENESIS_COLLECT", "").strip().lower() in ("1", "true", "yes")
    print("LYGO Heartbeats ONLY — sentinel every 5 min (Ctrl+C to stop)")
    if collect:
        print("  LYGO_GENESIS_COLLECT=1 — will also run genesis collector")
    else:
        print("  collector OFF (set LYGO_GENESIS_COLLECT=1 to enable)")
    while True:
        try:
            run_python(SENTINEL, timeout=240)
            if collect and GENESIS_COLLECTOR.is_file():
                run_python(GENESIS_COLLECTOR, timeout=300)
        except Exception as exc:
            print(f"[heartbeat] {exc}")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Heartbeats stopped.")
        raise SystemExit(0)
