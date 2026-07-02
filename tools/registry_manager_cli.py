#!/usr/bin/env python3
"""Deprecated — use tools/registry_manager.py or tools/cas_registry_cli.py status."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    argv = [sys.executable, str(ROOT / "tools" / "registry_manager.py"), *sys.argv[1:]]
    if len(sys.argv) == 1:
        argv.append("--status")
    raise SystemExit(subprocess.call(argv, cwd=ROOT))