#!/usr/bin/env python3
"""ClawHub mirror — delegate to stack joy_loop_planter."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _stack_paths import stack_root  # noqa: E402

ROOT = stack_root()
cmd = [sys.executable, str(ROOT / "tools" / "joy_loop_planter.py"), "--i-consent"]
raise SystemExit(subprocess.call(cmd, cwd=ROOT))