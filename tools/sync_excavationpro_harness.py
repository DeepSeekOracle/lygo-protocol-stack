#!/usr/bin/env python3
"""Copy canonical BiometricEntropyHarness.html to local Excavationpro repo (Pages mirror)."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "BiometricEntropyHarness.html"
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
            f"  git clone https://github.com/DeepSeekOracle/Excavationpro.git \"{args.dest}\"",
            file=sys.stderr,
        )
        return 1

    dst = args.dest / "BiometricEntropyHarness.html"
    shutil.copy2(SRC, dst)
    print(f"Copied → {dst}")

    if args.push:
        subprocess.run(["git", "add", str(dst.name)], cwd=args.dest, check=False)
        subprocess.run(
            ["git", "commit", "-m", "sync: BiometricEntropyHarness from lygo-protocol-stack docs"],
            cwd=args.dest,
            check=False,
        )
        return subprocess.call(["git", "push"], cwd=args.dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())