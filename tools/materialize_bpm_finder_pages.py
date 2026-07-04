#!/usr/bin/env python3
"""Publish stack + Excavationpro BPM Finder pages from canonical docs/LYGO_BPM_Finder.html."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STACK = ROOT / "docs" / "LYGO_BPM_Finder.html"
EXCA = ROOT.parent / "Excavationpro" / "LYGOBPMFinder.html"

STACK_CANONICAL = "https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_BPM_Finder.html"
EXCA_CANONICAL = "https://deepseekoracle.github.io/Excavationpro/LYGOBPMFinder.html"

STACK_FOOTER = """
<p class="site-footer">
  <strong>Privacy:</strong> <a href="https://www.npmjs.com/package/bpm-detective" rel="noopener noreferrer" target="_blank">bpm-detective</a> runs locally — no server upload.
  · <a href="index.html">LYGO stack index</a>
  · <a href="https://deepseekoracle.github.io/Excavationpro/eternalhaven.html">Main hub</a>
  · <a href="https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/BIOPHASE7_BPM_FINDER.md">Spec</a>
</p>"""

EXCA_FOOTER = """
<p class="site-footer">
  <strong>Privacy:</strong> <a href="https://www.npmjs.com/package/bpm-detective" rel="noopener noreferrer" target="_blank">bpm-detective</a> runs locally — no server upload.
  · <a href="eternalhaven.html">Eternal Haven hub</a>
  · <a href="LYGORESONANCE.html">LYGO Resonance</a>
  · <a href="https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/BIOPHASE7_BPM_FINDER.md">Spec</a>
</p>"""


def patch_mirror(html: str, *, canonical: str, site_name: str, footer: str) -> str:
    html = re.sub(
        r'<link rel="canonical" href="[^"]+">',
        f'<link rel="canonical" href="{canonical}">',
        html,
        count=1,
    )
    html = re.sub(
        r'<meta property="og:site_name" content="[^"]+">',
        f'<meta property="og:site_name" content="{site_name}">',
        html,
        count=1,
    )
    html = re.sub(
        r'<meta property="og:url" content="[^"]+">',
        f'<meta property="og:url" content="{canonical}">',
        html,
        count=1,
    )
    html = re.sub(
        r'"url": "https://deepseekoracle\.github\.io/[^"]+"',
        f'"url": "{canonical}"',
        html,
        count=1,
    )
    html = re.sub(
        r"<p class=\"site-footer\">.*?</p>",
        footer.strip(),
        html,
        count=1,
        flags=re.DOTALL,
    )
    return html


def main() -> int:
    if not STACK.is_file():
        raise SystemExit(f"Missing canonical page: {STACK}")
    base = STACK.read_text(encoding="utf-8")
    if base.count("<!DOCTYPE") != 1 or "bpm-detective" not in base:
        raise SystemExit("LYGO_BPM_Finder.html looks corrupt — fix before materialize")

    print("OK stack canonical", STACK)
    if EXCA.parent.is_dir():
        exca_html = patch_mirror(
            base,
            canonical=EXCA_CANONICAL,
            site_name="Excavationpro / LYGO",
            footer=EXCA_FOOTER,
        )
        EXCA.write_text(exca_html, encoding="utf-8")
        print("Wrote", EXCA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())