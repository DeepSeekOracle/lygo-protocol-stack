#!/usr/bin/env python3
"""Build lygo-champion-council mirror roster from egg registry + council extract."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIRROR = ROOT / "clawhub" / "mirrors" / "lygo-champion-council" / "references"


def main() -> int:
    reg = json.loads((ROOT / "data/champion_eggs/registry.json").read_text(encoding="utf-8"))
    council = json.loads((ROOT / "data/champion_eggs/champions_council.json").read_text(encoding="utf-8"))
    by_short = {c["short"]: c for c in council["champions"]}
    roster = []
    for e in reg["eggs"]:
        cid = e["champion_id"]
        meta = by_short.get(cid) or {}
        egg = e["egg_id"]
        roster.append(
            {
                "champion_id": cid,
                "egg_id": egg,
                "name": meta.get("name", cid),
                "role": meta.get("role", ""),
                "merkle_root": e.get("merkle_root", ""),
            }
        )
    out = {
        "signature": "Δ9Φ963-COUNCIL-ROSTER-v1",
        "count": len(roster),
        "council_merkle_root": reg["council_merkle_root"],
        "champions": roster,
    }
    MIRROR.mkdir(parents=True, exist_ok=True)
    (MIRROR / "council_roster.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "count": len(roster)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())