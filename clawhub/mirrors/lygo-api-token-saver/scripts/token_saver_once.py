#!/usr/bin/env python3
"""Cron-friendly token saver tick: status + optional army self-tune hook."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HUB = HERE / "token_saver_hub.py"


def main() -> int:
    cp = subprocess.run([sys.executable, str(HUB), "--status"], capture_output=True, text=True, timeout=60)
    if cp.returncode != 0:
        print(cp.stderr or cp.stdout)
        return cp.returncode
    status = json.loads(cp.stdout or "{}")
    if not status.get("ollama_ok"):
        print(json.dumps({"verdict": "OLLAMA_OFFLINE", "status": status}, indent=2))
        return 1
    print(json.dumps({"verdict": "TOKEN_SAVER_OK", "status": status}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())