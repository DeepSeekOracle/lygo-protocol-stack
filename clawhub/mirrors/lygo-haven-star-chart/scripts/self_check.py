#!/usr/bin/env python3
"""Mirror install smoke check for lygo-haven-star-chart."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STACK = Path(os.environ.get("LYGO_STACK_ROOT", "")).expanduser()

REQ = [
    ROOT / "SKILL.md",
    ROOT / "references" / "AGENT_CONTRACT.md",
    ROOT / "references" / "SECURITY.md",
    ROOT / "references" / "SUBMISSION_TRAINING.md",
    ROOT / "scripts" / "_stack_paths.py",
    ROOT / "scripts" / "gate_submission.py",
    ROOT / "scripts" / "verify_feed.py",
    ROOT / "scripts" / "agent_flow.py",
]
missing = [str(p) for p in REQ if not p.exists()]
if missing:
    print("MISSING", missing)
    raise SystemExit(2)

if STACK.is_dir():
    stack_req = [
        STACK / "tools" / "haven_star_chart_gate.py",
        STACK / "tools" / "haven_star_chart_feed.py",
        STACK / "docs" / "haven_star_chart" / "haven_star_chart_feed.json",
    ]
    miss = [str(p) for p in stack_req if not p.exists()]
    if miss:
        print("WARN stack", miss)
    else:
        cp = subprocess.run(
            [sys.executable, str(STACK / "tools" / "haven_star_chart_feed.py"), "--verify"],
            cwd=STACK,
            capture_output=True,
            text=True,
        )
        if cp.returncode != 0:
            print("WARN feed chain", cp.stdout or cp.stderr)
        else:
            print("OK feed chain")
else:
    print("OK mirror (set LYGO_STACK_ROOT for stack paths)")

print("OK lygo-haven-star-chart self_check")
raise SystemExit(0)