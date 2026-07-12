#!/usr/bin/env python3
"""Copy Haven Star Chart hub to local Excavationpro repo (GitHub Pages)."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_HTML = ROOT / "docs" / "HavenStarChart.html"
CANONICAL_PORTAL = ROOT / "docs" / "HavenStarChartPortal.html"
CANONICAL_DATA = ROOT / "docs" / "haven_star_chart"
CANONICAL_ASSETS = ROOT / "docs" / "assets"
DEFAULT_DEST = ROOT.parent / "Excavationpro"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    ap.add_argument("--push", action="store_true")
    args = ap.parse_args()

    if not CANONICAL_HTML.is_file():
        print("Run tools/build_haven_star_chart.py first", file=sys.stderr)
        return 2

    dest = args.dest
    if not dest.is_dir():
        print(f"Clone Excavationpro to {dest}", file=sys.stderr)
        return 1

    out_html = dest / "HavenStarChart.html"
    out_portal = dest / "HavenStarChartPortal.html"
    out_dir = dest / "haven_star_chart"
    out_assets = dest / "assets"
    shutil.copy2(CANONICAL_HTML, out_html)
    if CANONICAL_PORTAL.is_file():
        shutil.copy2(CANONICAL_PORTAL, out_portal)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(CANONICAL_DATA, out_dir)
    out_assets.mkdir(parents=True, exist_ok=True)
    for name in ("og-haven-star-chart.jpg", "og-haven-star-portal.jpg"):
        src = CANONICAL_ASSETS / name
        if src.is_file():
            shutil.copy2(src, out_assets / name)
    print(f"Synced → {out_html}, {out_portal}, {out_dir}, assets/")

    print(
        "NOTE: Excavationpro may fail full git checkout on Windows (invalid path "
        "'LYGO-Network/Deep-Seek-Oracle /EIDOLON.html'). Prefer stack Pages hub or "
        "upload HavenStarChart.html + haven_star_chart/ via GitHub web UI.",
    )

    if args.push:
        subprocess.run(
            ["git", "add", "HavenStarChart.html", "HavenStarChartPortal.html", "haven_star_chart/", "assets/og-haven-star-chart.jpg", "assets/og-haven-star-portal.jpg"],
            cwd=dest,
            check=False,
        )
        subprocess.run(
            ["git", "commit", "-m", "seo: Haven Star Chart v2 + Agent Portal meta and feed sync"],
            cwd=dest,
            check=False,
        )
        subprocess.run(["git", "push", "origin", "main"], cwd=dest, check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())