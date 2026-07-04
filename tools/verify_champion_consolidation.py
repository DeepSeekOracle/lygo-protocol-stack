#!/usr/bin/env python3
"""Verify champion consolidation: council roster + legacy deprecated metadata."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIRRORS = ROOT / "clawhub" / "mirrors"
SUCCESSOR = "lygo-champion-council"
KEEP = "lygo-champion-lightfather"


def main() -> int:
    ok = True
    roster = MIRRORS / SUCCESSOR / "references" / "council_roster.json"
    if not roster.is_file():
        print("FAIL missing council_roster.json")
        return 2
    data = json.loads(roster.read_text(encoding="utf-8"))
    if data.get("count", 0) < 15:
        print("FAIL roster count", data.get("count"))
        ok = False
    else:
        print("OK roster count", data["count"])

    for mirror in sorted(MIRRORS.glob("lygo-champion-*")):
        slug = mirror.name
        if slug == SUCCESSOR:
            continue
        skill = (mirror / "SKILL.md").read_text(encoding="utf-8")
        if slug == KEEP:
            if "operator-only" not in skill and "operator stack" not in skill.lower():
                print(f"FAIL {slug} missing operator-only consolidation")
                ok = False
            continue
        if '"deprecated": true' not in skill and "DEPRECATED" not in skill:
            print(f"FAIL {slug} not deprecated")
            ok = False
        if SUCCESSOR not in skill:
            print(f"FAIL {slug} missing successor pointer")
            ok = False
    print("verdict=ALIGNED" if ok else "verdict=NEEDS_FIX")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())