#!/usr/bin/env python3
"""Install LPIS mirror + Biophase7 sync."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
BIOPHASE7 = WORKSPACE / "LYRA SYSTEM RETORE" / "FINAL RESTORE" / "ALL SEALS" / "220+" / "New folder" / "2026Biophase7"
GROK = WORKSPACE / ".grok" / "skills" / "lygo-lpis"
MIRROR = ROOT / "clawhub" / "mirrors" / "lygo-lpis"
DATA = ROOT / "data" / "prompt_vault"


def main() -> int:
    (DATA).mkdir(parents=True, exist_ok=True)
    if MIRROR.is_dir():
        GROK.parent.mkdir(parents=True, exist_ok=True)
        if GROK.exists():
            shutil.rmtree(GROK)
        shutil.copytree(MIRROR, GROK)
        print("grok:", GROK)
    if BIOPHASE7.is_dir():
        dest = BIOPHASE7 / "lygo-lpis-LYGO"
        src = ROOT / "lygo_lpis"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        shutil.copy2(ROOT / "docs" / "BIOPHASE7_LYGO_LPIS.md", BIOPHASE7 / "LYGO_LPIS_INSTALLED.md")
        note = BIOPHASE7 / "This is a massive opportunity for L. LYGO-INSTALLED.txt"
        note.write_text(f"LPIS installed from {ROOT}\nSee LYGO_LPIS_INSTALLED.md\n", encoding="utf-8")
        print("biophase7:", dest)
    print("OK install_lygo_lpis")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())