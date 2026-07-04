"""Self-check for LYGO Champion: Lightfather skill pack."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQ = [
    ROOT / "SKILL.md",
    ROOT / "references" / "canon.json",
    ROOT / "references" / "persona_pack.md",
    ROOT / "references" / "stack_integration.md",
    ROOT / "references" / "seals_and_failsafe.md",
    ROOT / "references" / "verifier_usage.md",
    ROOT / "references" / "SECURITY.md",
]

missing = [str(p) for p in REQ if not p.exists()]
if missing:
    print("MISSING_FILES:")
    for m in missing:
        print(" -", m)
    raise SystemExit(3)

canon = json.loads((ROOT / "references" / "canon.json").read_text(encoding="utf-8"))
if canon.get("champion") != "Lightfather":
    print("BAD_CANON: champion != Lightfather")
    raise SystemExit(2)

h = canon.get("lygo_mint_sha256")
if not isinstance(h, str) or len(h) != 64:
    print("BAD_CANON: lygo_mint_sha256 missing/invalid")
    raise SystemExit(2)

vu = (ROOT / "references" / "verifier_usage.md").read_text(encoding="utf-8", errors="replace")
if "lygo-mint-verifier" not in vu:
    print("BAD_REF: verifier link missing")
    raise SystemExit(2)

print("OK")
print("HASH", h)
print("EGG", canon.get("kernel_egg_id"))