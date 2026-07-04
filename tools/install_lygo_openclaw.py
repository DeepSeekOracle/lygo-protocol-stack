#!/usr/bin/env python3
"""Install LYGO-OpenClaw + sync hybrid lyra-openclaw skills."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
BIOPHASE7 = WORKSPACE / "LYRA SYSTEM RETORE" / "FINAL RESTORE" / "ALL SEALS" / "220+" / "New folder" / "2026Biophase7"
GROK_LYGO = WORKSPACE / ".grok" / "skills" / "lygo-openclaw"
GROK_LYRA = WORKSPACE / ".grok" / "skills" / "lyra-openclaw"
MIRROR_LYGO = ROOT / "clawhub" / "mirrors" / "lygo-openclaw"
MIRROR_LYRA = ROOT / "clawhub" / "mirrors" / "lyra-openclaw"
DATA = ROOT / "data" / "openclaw"


def sync_skill(mirror: Path, dest: Path) -> str:
    if not mirror.is_dir():
        return f"skip:{mirror}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(mirror, dest)
    return str(dest)


def sync_biophase7() -> str:
    if not BIOPHASE7.is_dir():
        return "biophase7:skip"
    dest = BIOPHASE7 / "lygo-openclaw-LYGO"
    src = ROOT / "lygo_openclaw"
    if dest.exists():
        try:
            shutil.rmtree(dest)
        except OSError as e:
            return f"biophase7:rmtree-failed:{e}"
    shutil.copytree(src, dest)
    shutil.copy2(
        ROOT / "docs" / "BIOPHASE7_LYGO_OPENCLAW.md",
        BIOPHASE7 / "LYGO_OPENCLAW_INSTALLED.md",
    )
    note = BIOPHASE7 / "LYGO-OpenClaw. LYGO-INSTALLED.txt"
    note.write_text(
        f"LYGO-OpenClaw installed from stack {ROOT}\nSee LYGO_OPENCLAW_INSTALLED.md\n",
        encoding="utf-8",
    )
    return str(dest)


def main() -> int:
    for sub in ("mycelium", "runs"):
        (DATA / sub).mkdir(parents=True, exist_ok=True)
    print("lygo-openclaw:", sync_skill(MIRROR_LYGO, GROK_LYGO))
    print("lyra-openclaw:", sync_skill(MIRROR_LYRA, GROK_LYRA))
    print(sync_biophase7())
    print("OK install_lygo_openclaw")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())