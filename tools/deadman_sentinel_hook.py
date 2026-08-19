#!/usr/bin/env python3
"""Sentinel → deadman touch hook (consent-local).

Call from army/sentinel after a healthy steward pulse:
  python tools/deadman_sentinel_hook.py --source army-sentinel
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="sentinel-hook")
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    cmd = [sys.executable, str(ROOT / "tools" / "seal_deadman_lattice.py")]
    if args.check_only:
        cmd.append("status")
    else:
        cmd.append("touch")
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    print(r.stdout)
    if r.stderr:
        print(r.stderr, file=sys.stderr)
    # annotate source in heartbeat log via status path already; extra note file
    note = {
        "hook": "deadman_sentinel_hook",
        "source": args.source,
        "ok": r.returncode == 0,
    }
    out = ROOT / "data" / "deadman" / "sentinel_hook_last.json"
    out.write_text(json.dumps(note, indent=2) + "\n", encoding="utf-8")
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
