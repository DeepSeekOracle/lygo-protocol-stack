#!/usr/bin/env python3
"""Skill wrapper — run haven_star_chart_gate.py on a submission file."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from _stack_paths import resolve_stack_root


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: gate_submission.py <submission.json>")
        return 2
    root = resolve_stack_root()
    script = root / "tools" / "haven_star_chart_gate.py"
    cp = subprocess.run([sys.executable, str(script), sys.argv[1]], cwd=root, check=False)
    return cp.returncode


if __name__ == "__main__":
    raise SystemExit(main())