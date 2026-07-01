#!/usr/bin/env python3
"""Bundle Grokipedia upload payload (manual paste — no autonomous Grokipedia API)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "GROkipedia_UPLOAD_BUNDLE.md"
PARTS = [
    ROOT / "docs" / "PHASE2_DEPLOYMENT.md",
    ROOT / "docs" / "GROkipedia_PHASE3.md",
    ROOT / "docs" / "BLUEPRINT.md",
]

HEADER = """# LYGO Protocol Stack — Grokipedia upload bundle

**Operator:** Copy sections below into https://grokipedia.com/page/lygo-protocol-stack  
**Signature:** Δ9Φ963-EXECUTION-DAG-v1.0  
**Do not include secrets or tokens.**

---

"""


def main() -> int:
    chunks = [HEADER]
    for p in PARTS:
        if p.is_file():
            chunks.append(f"\n\n<!-- SOURCE: {p.name} -->\n\n")
            chunks.append(p.read_text(encoding="utf-8"))
    OUT.write_text("".join(chunks), encoding="utf-8")
    print(f"Wrote {OUT}")
    print("Human step: paste into Grokipedia editor and publish.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())