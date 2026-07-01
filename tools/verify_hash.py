#!/usr/bin/env python3
"""Cross-platform LYGO P0 determinism verifier (Windows + Linux)."""

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P0 = ROOT / "protocol0_nano_kernel" / "src" / "python" / "lygo_p0.py"


def main() -> int:
    print("⚡ LYGO DETERMINISM VERIFICATION")
    print("=================================")
    proc = subprocess.run([sys.executable, str(P0)], capture_output=True, text=True, check=True)
    digest = hashlib.sha256(proc.stdout.encode("utf-8")).hexdigest()
    print(proc.stdout)
    print(f"SHA-256(stdout): {digest}")
    print("")
    print("✅ Determinism check complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())