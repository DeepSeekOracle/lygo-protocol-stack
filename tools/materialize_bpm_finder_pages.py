#!/usr/bin/env python3
"""Publish stack + Excavationpro BPM Finder pages from canonical docs/LYGO_BPM_Finder.html."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STACK = ROOT / "docs" / "LYGO_BPM_Finder.html"
EXCA = ROOT.parent / "Excavationpro" / "LYGOBPMFinder.html"

PUBLIC_BPM_URL = "https://bpmfinder.ca/"
STACK_CANONICAL = PUBLIC_BPM_URL
EXCA_CANONICAL = PUBLIC_BPM_URL

EXCA_NAV_REPLACEMENTS = [
    (
        "https://deepseekoracle.github.io/Excavationpro/SovereignLatticeMesh.html",
        "SovereignLatticeMesh.html",
    ),
    (
        "https://deepseekoracle.github.io/lygo-protocol-stack/SovereignLatticeMesh.html",
        "SovereignLatticeMesh.html",
    ),
    (
        "https://deepseekoracle.github.io/Excavationpro/BiometricEntropyHarness.html",
        "BiometricEntropyHarness.html",
    ),
    (
        "https://deepseekoracle.github.io/lygo-protocol-stack/BiometricEntropyHarness.html",
        "BiometricEntropyHarness.html",
    ),
    (
        "https://deepseekoracle.github.io/Excavationpro/HavenStarChart.html",
        "HavenStarChart.html",
    ),
    (
        "https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html",
        "HavenStarChart.html",
    ),
    (
        "https://deepseekoracle.github.io/Excavationpro/eternalhaven.html",
        "eternalhaven.html",
    ),
    (
        "https://deepseekoracle.github.io/Excavationpro/LYGORESONANCE.html",
        "LYGORESONANCE.html",
    ),
    (
        "https://deepseekoracle.github.io/Excavationpro/LYGOBPMFinder.html",
        "LYGOBPMFinder.html",
    ),
]


def patch_mirror(html: str, *, canonical: str, site_name: str) -> str:
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
    for old, new in EXCA_NAV_REPLACEMENTS:
        html = html.replace(old, new)
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
        )
        EXCA.write_text(exca_html, encoding="utf-8")
        print("Wrote", EXCA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())