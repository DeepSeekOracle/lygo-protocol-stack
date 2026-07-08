#!/usr/bin/env python3
"""Copy canonical LYGO_BPM_Finder.html to Excavationpro as LYGOBPMFinder.html."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "LYGO_BPM_Finder.html"
DEST_NAME = "LYGOBPMFinder.html"
DEFAULT_DEST = ROOT.parent / "Excavationpro"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    ap.add_argument("--push", action="store_true", help="git commit + push dest repo")
    args = ap.parse_args()

    if not SRC.is_file():
        print(f"Missing {SRC}", file=sys.stderr)
        return 1
    if not args.dest.is_dir():
        print(
            f"Clone Excavationpro next to lygo-protocol-stack:\n"
            f'  git clone https://github.com/DeepSeekOracle/Excavationpro.git "{args.dest}"',
            file=sys.stderr,
        )
        return 1

    dst = args.dest / DEST_NAME
    mat = ROOT / "tools" / "materialize_bpm_finder_pages.py"
    if mat.is_file():
        subprocess.run([sys.executable, str(mat)], check=True)
    if not dst.is_file():
        print(f"Missing {dst} after materialize", file=sys.stderr)
        return 1
    print(f"Copied → {dst}")

    if args.push:
        subprocess.run(["git", "add", DEST_NAME], cwd=args.dest, check=False)
        subprocess.run(
            ["git", "commit", "-m", "sync: LYGOBPMFinder from lygo-protocol-stack docs"],
            cwd=args.dest,
            check=False,
        )
        return subprocess.call(["git", "push"], cwd=args.dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())