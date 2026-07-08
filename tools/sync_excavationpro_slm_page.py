#!/usr/bin/env python3
"""Sync SovereignLatticeMesh.html — canonical in lygo-protocol-stack/docs ↔ Excavationpro mirror."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "docs" / "SovereignLatticeMesh.html"
DEFAULT_DEST = ROOT.parent / "Excavationpro"
FETCH_FALLBACK = ROOT / "docs" / "_slm_fetch.html"


def ensure_canonical() -> int:
    if CANONICAL.is_file():
        return 0
    if FETCH_FALLBACK.is_file():
        shutil.copy2(FETCH_FALLBACK, CANONICAL)
        print(f"Seeded canonical from fetch → {CANONICAL}")
        return 0
    print(
        "Missing docs/SovereignLatticeMesh.html — fetch from:\n"
        "  https://raw.githubusercontent.com/DeepSeekOracle/Excavationpro/main/SovereignLatticeMesh.html",
        file=sys.stderr,
    )
    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    ap.add_argument("--push", action="store_true", help="git commit + push Excavationpro")
    ap.add_argument("--from-upstream", action="store_true", help="Refresh canonical from docs/_slm_fetch.html if present")
    args = ap.parse_args()

    if args.from_upstream and FETCH_FALLBACK.is_file():
        shutil.copy2(FETCH_FALLBACK, CANONICAL)

    if ensure_canonical() != 0:
        return 1

    if not args.dest.is_dir():
        print(
            f"Optional mirror: clone Excavationpro to {args.dest}\n"
            f"  git clone https://github.com/DeepSeekOracle/Excavationpro.git",
            file=sys.stderr,
        )
        return 0

    dst = args.dest / "SovereignLatticeMesh.html"
    shutil.copy2(CANONICAL, dst)
    print(f"Copied canonical → {dst}")

    if args.push:
        subprocess.run(["git", "add", dst.name], cwd=args.dest, check=False)
        subprocess.run(
            ["git", "commit", "-m", "sync: SovereignLatticeMesh from lygo-protocol-stack docs"],
            cwd=args.dest,
            check=False,
        )
        return subprocess.call(["git", "push"], cwd=args.dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())