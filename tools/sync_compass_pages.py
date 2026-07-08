#!/usr/bin/env python3
"""Copy canonical tools/LYGO_Compass_Master.html → docs/tools/ for GitHub Pages."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "tools" / "LYGO_Compass_Master.html"
DST_DIR = REPO / "docs" / "tools"
DST = DST_DIR / "LYGO_Compass_Master.html"


def main() -> int:
    if not SRC.is_file():
        print(f"SKIP: canonical missing — {SRC}")
        print("Add or build LYGO_Compass_Master.html under tools/, then re-run.")
        return 0
    DST_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC, DST)
    print(f"OK: {SRC} → {DST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())