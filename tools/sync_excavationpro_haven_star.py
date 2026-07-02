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
CANONICAL_DATA = ROOT / "docs" / "haven_star_chart"
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
    out_dir = dest / "haven_star_chart"
    shutil.copy2(CANONICAL_HTML, out_html)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(CANONICAL_DATA, out_dir)
    print(f"Synced → {out_html} and {out_dir}")

    if args.push:
        subprocess.run(["git", "add", "HavenStarChart.html", "haven_star_chart"], cwd=dest, check=False)
        subprocess.run(
            ["git", "commit", "-m", "feat: Eternal Haven Star Chart hub (LYGO stack sync)"],
            cwd=dest,
            check=False,
        )
        subprocess.run(["git", "push", "origin", "main"], cwd=dest, check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())