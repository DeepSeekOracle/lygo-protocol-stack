#!/usr/bin/env python3
"""Plugin bundle smoke check — no subprocess in plugin runtime."""

from __future__ import annotations

import json
from pathlib import Path

from _stack_paths import resolve_stack_root
from _stack_tools import load_tool

ROOT = Path(__file__).resolve().parents[1]

REQ = [
    ROOT / "openclaw.plugin.json",
    ROOT / "references" / "SECURITY.md",
    ROOT / "references" / "SKILLSPECTOR_AUDIT.md",
    ROOT / "scripts" / "_stack_paths.py",
    ROOT / "scripts" / "_stack_tools.py",
    ROOT / "scripts" / "gate_submission.py",
]
missing = [str(p) for p in REQ if not p.exists()]
if missing:
    print("MISSING", missing)
    raise SystemExit(2)

try:
    stack = resolve_stack_root()
except SystemExit:
    print("OK plugin bundle (set LYGO_STACK_ROOT to run stack verify)")
else:
    gate = load_tool(stack, "haven_star_chart_gate.py")
    print(json.dumps({"stack": str(stack), "gate_loaded": bool(gate)}))

print("OK lygo-lattice-pulse self_check")
raise SystemExit(0)