#!/usr/bin/env python3
"""Seeder-side wrapper: prefer stack unified verify; else sovereign-only."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    stack = os.environ.get("LYGO_STACK_ROOT", "").strip()
    if stack:
        tool = Path(stack) / "tools" / "verify_all_kernel_layers.py"
        if tool.is_file():
            return subprocess.call([sys.executable, str(tool), *sys.argv[1:]], cwd=stack)
    # fallback sovereign only
    root = os.environ.get("LYGO_SEED_ROOT", "").strip()
    cmd = [sys.executable, str(HERE / "verify_seed.py")]
    if root:
        cmd.extend(["--root", root])
    if "--json" in sys.argv:
        cmd.append("--json")
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
