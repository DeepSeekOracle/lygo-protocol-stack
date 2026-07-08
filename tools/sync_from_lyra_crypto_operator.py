#!/usr/bin/env python3
"""Sync canonical lyra-crypto-operator tree into stack ClawHub mirror (publish stub only)."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPERATOR = ROOT.parent / "lyra-crypto-operator"
MIRROR = ROOT / "clawhub" / "mirrors" / "lyra-coin-launch-manager"
SKIP = {"README.md", ".git"}


def main() -> int:
    if not OPERATOR.is_dir():
        print(f"MISSING canonical repo: {OPERATOR}", file=sys.stderr)
        return 2
    MIRROR.mkdir(parents=True, exist_ok=True)
    for item in OPERATOR.iterdir():
        if item.name in SKIP:
            continue
        dest = MIRROR / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    stub = MIRROR / "SOURCE_CANONICAL.txt"
    stub.write_text(f"Canonical source: {OPERATOR}\nSync: python tools/sync_from_lyra_crypto_operator.py\n", encoding="utf-8")
    print(f'{{"ok": true, "mirror": "{MIRROR}", "operator": "{OPERATOR}"}}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())