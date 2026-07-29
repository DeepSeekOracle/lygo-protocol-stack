#!/usr/bin/env python3
"""
LYGO Ollama Heartbeats ONLY — sentinel pulse every 5 minutes.
No LLM daemons, no monitoring UI. Runs until Ctrl+C or window closed.
"""

from __future__ import annotations

import sys
from pathlib import Path as _P
_SKILL = _P(__file__).resolve().parents[2]
if str(_SKILL) not in sys.path:
    sys.path.insert(0, str(_SKILL))
from _safe_invoke import run_python, run_daemon_thread, git_status_summary, write_local_alert  # noqa: E402

import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SENTINEL = HERE / "sentinel_heartbeat.py"
GENESIS_COLLECTOR = HERE.parents[1] / "genesis_console" / "collector.py"
INTERVAL = 300


def main() -> int:
    print("LYGO Heartbeats ONLY — sentinel every 5 min (Ctrl+C to stop)")
    while True:
        try:
            run_python(SENTINEL, timeout=240)
            if GENESIS_COLLECTOR.is_file():
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