#!/usr/bin/env python3
"""Verify kit zip SHA-256. No network. No subprocess."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PIN = "b60ed6deae6f1dba7182fa386bd00b1e724001638e8f2f30936af0a240b4444e"
ZIP_NAME = "lygo-llm-console-public.zip"


def main() -> int:
    z = ROOT / "kit" / ZIP_NAME
    side = ROOT / "kit" / (ZIP_NAME + ".sha256")
    if not z.is_file():
        print(json.dumps({"ok": False, "error": "zip_missing", "path": str(z)}))
        return 1
    digest = hashlib.sha256(z.read_bytes()).hexdigest()
    pin = PIN
    if side.is_file():
        pin = side.read_text(encoding="utf-8").split()[0].strip() or PIN
    ok = digest.lower() == pin.lower() == PIN.lower()
    print(json.dumps({"ok": ok, "sha256": digest, "pinned": PIN, "bytes": z.stat().st_size}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
