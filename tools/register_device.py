#!/usr/bin/env python3
"""CLI — register a simulated biometric device with HAIP."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "stack"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", required=True, choices=["apple_watch", "garmin", "oura", "custom"])
    ap.add_argument("--id", required=True, dest="device_id")
    ap.add_argument("--connection", default="simulated")
    args = ap.parse_args()

    from lygo_stack import deploy_stack

    stack = deploy_stack("HAIP_CLI")
    out = stack.register_biometric_device(args.type, args.device_id, args.connection)
    print(json.dumps(out, indent=2))
    return 0 if out.get("status") == "registered" else 1


if __name__ == "__main__":
    raise SystemExit(main())