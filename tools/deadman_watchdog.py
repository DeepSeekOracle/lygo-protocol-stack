#!/usr/bin/env python3
"""Deadman heartbeat watchdog — basic real-life runner.

Modes:
  once     — status+grace; with --touch also resets transmit clock
  loop     — repeat every --interval seconds (Ctrl+C to stop)
  check    — status+grace only (never touch)

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
CLI = ROOT / "tools" / "seal_deadman_lattice.py"


def run_cmd(*args: str) -> dict:
    r = subprocess.run(
        [PY, str(CLI), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(r.stdout or "{}")
    except json.JSONDecodeError:
        payload = {"ok": r.returncode == 0, "raw": r.stdout, "err": r.stderr}
    if not isinstance(payload, dict):
        payload = {"ok": r.returncode == 0, "raw": payload}
    payload.setdefault("ok", r.returncode == 0)
    payload["_exit"] = r.returncode
    return payload


def tick(*, do_touch: bool) -> int:
    out: dict = {}
    if do_touch:
        out["touch"] = run_cmd("touch")
    out["status"] = run_cmd("status")
    out["grace"] = run_cmd("grace")
    # Surface alert tiers for operators / logs
    tier = (out.get("grace") or {}).get("tier")
    out["alert"] = tier in {"LANTERN", "WHISPER", "TORCHBEARER_WINDOW"}
    print(json.dumps(out, indent=2))
    status_ok = bool((out.get("status") or {}).get("ok"))
    touch_ok = True if not do_touch else bool((out.get("touch") or {}).get("ok", True))
    return 0 if status_ok and touch_ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO deadman watchdog")
    ap.add_argument("mode", choices=["once", "loop", "check"], default="once", nargs="?")
    ap.add_argument("--interval", type=int, default=300, help="loop interval seconds")
    ap.add_argument("--touch", action="store_true", help="reset transmit clock (origin activity)")
    args = ap.parse_args()

    do_touch = bool(args.touch) and args.mode != "check"

    if args.mode == "loop":
        code = 0
        while True:
            code = tick(do_touch=do_touch)
            time.sleep(max(30, int(args.interval)))
        return code
    return tick(do_touch=do_touch)


if __name__ == "__main__":
    raise SystemExit(main())
