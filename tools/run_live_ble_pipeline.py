#!/usr/bin/env python3
"""Install + start Biophase7 live BLE → WebSocket pipeline (Objective.txt)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO live BLE pipeline")
    ap.add_argument("--simulate-stream", action="store_true", help="No hardware; synthetic IBI on WS :8788")
    ap.add_argument("--ws-port", type=int, default=8788)
    ap.add_argument("--check-deps", action="store_true")
    args = ap.parse_args()

    req = ROOT / "requirements-p7-ble.txt"
    if args.check_deps:
        print(f"Install: pip install -r {req}")
        return 0

    cmd = [
        sys.executable,
        str(ROOT / "tools" / "live_ble_telemetry_ingest.py"),
        "--with-ws",
        "--ws-host",
        "0.0.0.0",
        "--ws-port",
        str(args.ws_port),
    ]
    if args.simulate_stream:
        cmd.append("--simulate-stream")

    print("Δ9Φ963 — Live BLE pipeline")
    print("  1) Tunnel port", args.ws_port, "→ set HF secret LYGO_BLE_WS_URL=wss://…")
    print("  2) HF Space tab: Live BLE stream")
    print("  3) Docs: docs/BIOPHASE7_OBJECTIVE_LIVE_BLE.md")
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())