#!/usr/bin/env python3
"""Deadman heartbeat watchdog — basic real-life runner.

Modes:
  once     — touch (if --touch) then status/grace
  loop     — repeat every --interval seconds (Ctrl+C to stop)
  check    — check silence / escalate locally only

Does not auto-publish. Does not claim identity.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run_cmd(*args: str) -> dict:
    r = subprocess.run([PY, str(ROOT / "tools" / "seal_deadman_lattice.py"), *args], cwd=str(ROOT), capture_output=True, text=True)
    try:
        return json.loads(r.stdout or "{}")
    except json.JSONDecodeError:
        return {"ok": r.returncode == 0, "raw": r.stdout, "err": r.stderr, "code": r.returncode}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["once", "loop", "check"], default="once", nargs="?")
    ap.add_argument("--interval", type=int, default=300, help="loop interval seconds")
    ap.add_argument("--touch", action="store_true", help="reset transmit clock (origin activity)")
    args = ap.parse_args()

    def tick() -> int:
        if args.touch or args.mode == "once":
            if args.touch:
                print(json.dumps({"touch": run_cmd("touch")}, indent=2))
        if args.mode == "check" or True:
            status = run_cmd("status")
            grace = run_cmd("grace")
            print(json.dumps({"status": status, "grace": grace}, indent=2))
            return 0 if status.get("ok") else 1
        return 0

    if args.mode == "loop":
        while True:
            tick()
            time.sleep(max(30, args.interval))
    return tick()


if __name__ == "__main__":
    raise SystemExit(main())
