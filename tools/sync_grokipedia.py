#!/usr/bin/env python3
"""Grokipedia ops: archive bundle + pointer to GROkipedia_SUBMIT.md and GitHub Pages."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "GROkipedia_UPLOAD_BUNDLE.md"
SUBMIT = ROOT / "docs" / "GROkipedia_SUBMIT.md"
PAGES_URL = "https://deepseekoracle.github.io/lygo-protocol-stack/"
PARTS = [
    ROOT / "docs" / "PHASE2_DEPLOYMENT.md",
    ROOT / "docs" / "GROkipedia_PHASE3.md",
    ROOT / "docs" / "BLUEPRINT.md",
]

HEADER = f"""# LYGO Protocol Stack — Grokipedia upload bundle (archive)

**Do not paste this whole file into Grokipedia.** Use **`docs/GROkipedia_SUBMIT.md`** (title + brief + links).

**Public reference (GitHub Pages):** {PAGES_URL}  
**Repo:** https://github.com/DeepSeekOracle/lygo-protocol-stack  
**Signature:** Δ9Φ963-EXECUTION-DAG-v1.0

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
    print(f"Grokipedia form: {SUBMIT}")
    print(f"Pages URL (after deploy): {PAGES_URL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())