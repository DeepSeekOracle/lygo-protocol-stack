#!/usr/bin/env python3
"""Rebuild public Lightfather style fingerprints from public canon sources."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    # Harden rebuilds fingerprints; then bump pins with consent if operator asks
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "harden_deadman_continuity.py")], cwd=str(ROOT))
    print("retrain_via_harden_exit", r.returncode)
    print("Next (if pins should update): python tools/bump_deadman_origin_pins.py --i-consent --note style-retrain")
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
