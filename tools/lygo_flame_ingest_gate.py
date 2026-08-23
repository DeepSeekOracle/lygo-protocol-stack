#!/usr/bin/env python3
"""LYGO Flame ingest gate — stack entrypoint before authority promotion.

Wraps clawhub/mirrors/lygo-flame-ward (in-process). No subprocess. No network.

Exit: 0 CLEAR · 5 UNVERIFIED/HALF_TRUTH · 10 QUARANTINE · 1 error
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

STACK = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = STACK / "clawhub" / "mirrors" / "lygo-flame-ward" / "scripts"


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO Flame ingest gate")
    ap.add_argument("--text", default="")
    ap.add_argument("--text-file", default="")
    ap.add_argument("--skill-dir", default="")
    ap.add_argument("--write", default=None)
    ap.add_argument("--i-consent", action="store_true")
    args = ap.parse_args()

    if not SKILL_SCRIPTS.is_dir():
        print(json.dumps({"ok": False, "error": f"missing flame ward at {SKILL_SCRIPTS}"}))
        return 1

    sys.path.insert(0, str(SKILL_SCRIPTS))
    import flame_cli as fc  # noqa: E402

    out = fc.cmd_ingest_gate(args)
    print(json.dumps(out, indent=2))
    if out.get("ok") is False:
        return 1
    v = out.get("verdict")
    if v == "QUARANTINE":
        return 10
    if v in {"HALF_TRUTH", "UNVERIFIED"}:
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
