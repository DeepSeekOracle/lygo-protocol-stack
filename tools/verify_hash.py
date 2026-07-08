#!/usr/bin/env python3
"""LYGO P0 determinism verifier — delegates to vector suite + golden SHA."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARITY = ROOT / "tools" / "p0_crosslang_parity.py"


def main() -> int:
    print("⚡ LYGO P0 DETERMINISM (42-vector suite)")
    print("=================================")
    return subprocess.call([sys.executable, str(PARITY)])


if __name__ == "__main__":
    raise SystemExit(main())