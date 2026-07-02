#!/usr/bin/env python3
"""
LYGO Phase 7 — Live BLE telemetry ingest (GATT 0x180D).
Signature: Δ9Φ963-PHASE7-BLE-LIVE-HARNESS
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "tools" / "lygo_control_center" / "workspace"
WORKSPACE.mkdir(parents=True, exist_ok=True)
SEED_JSON = WORKSPACE / "latest_seed.json"
BUFFER_THRESHOLD = 64

sys.path.insert(0, str(ROOT))

from protocol7_human_ai_interface.ble_gatt import (  # noqa: E402
    HR_MEASUREMENT_CHAR_UUID,
    HR_SERVICE_UUID,
    bleak_available,
    parse_heart_rate_measurement,
)
from protocol7_human_ai_interface.entropy_extraction import extract_p0_seed_from_ibi  # noqa: E402

ENTROPY_BUFFER: list[int] = []


def _flush_seed(ibi: list[int]) -> dict:
    pack = extract_p0_seed_from_ibi([float(x) for x in ibi])
    payload = {
        "timestamp": time.time(),
        "signature": "Δ9Φ963-PHASE7-BLE-LIVE-HARNESS",
        "ibi_count": len(ibi),
        "h_min": pack.get("h_min"),
        "seed_256": pack.get("seed_256"),
        "seed_preview": str(pack.get("seed_256", ""))[:16],
    }
    SEED_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def handle_notification(data: bytes) -> None:
    global ENTROPY_BUFFER
    parsed = parse_heart_rate_measurement(data)
    for ibi in parsed.get("ibi_ms") or []:
        ENTROPY_BUFFER.append(int(ibi))
        print(f"[+] IBI: {ibi}ms | buffer {len(ENTROPY_BUFFER)}/{BUFFER_THRESHOLD}")
    if len(ENTROPY_BUFFER) >= BUFFER_THRESHOLD:
        print("[!] Threshold reached — extracting P0 seed...")
        out = _flush_seed(ENTROPY_BUFFER.copy())
        print(f"[>] H_min={out['h_min']} seed={out['seed_preview']}…")
        ENTROPY_BUFFER.clear()


async def _live_loop(scan_timeout: float = 8.0) -> int:
    from bleak import BleakClient, BleakScanner

    print("=" * 70)
    print("LYGO PHASE 7 — LIVE BLE TELEMETRY INGEST")
    print("Δ9Φ963-PHASE7-BLE-LIVE-HARNESS")
    print("=" * 70)
    devices = await BleakScanner.discover(timeout=scan_timeout)
    target = None
    for d in devices:
        uuids = (d.metadata or {}).get("uuids") or []
        if HR_SERVICE_UUID in uuids or (d.name and "heart" in d.name.lower()):
            target = d
            print(f"[+] Candidate: {d.name} [{d.address}]")
            break
    if target is None and devices:
        target = devices[0]
        print(f"[*] No HR service UUID — trying first device: {target.name} [{target.address}]")
    if target is None:
        print("[-] No BLE devices found.")
        return 1

    def _cb(_sender, data: bytearray) -> None:
        handle_notification(bytes(data))

    async with BleakClient(target.address) as client:
        await client.start_notify(HR_MEASUREMENT_CHAR_UUID, _cb)
        print(f"[+] Subscribed to {HR_MEASUREMENT_CHAR_UUID} — Ctrl+C to stop")
        while True:
            await asyncio.sleep(1)


def run_simulated_flush(n: int = 64) -> dict:
    """No hardware: synthetic IBI burst for dashboard / audit."""
    import random

    rng = random.Random(528963)
    ibi = [int(60000 / 75 + rng.uniform(-40, 40)) for _ in range(n)]
    return _flush_seed(ibi)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--simulate", action="store_true", help="Write seed from synthetic IBI (no BLE)")
    ap.add_argument("--scan-timeout", type=float, default=8.0)
    args = ap.parse_args()

    if args.simulate:
        out = run_simulated_flush()
        print(json.dumps(out, indent=2))
        return 0

    if not bleak_available():
        print("bleak not installed — pip install bleak  OR  use --simulate", file=sys.stderr)
        return 1

    try:
        return asyncio.run(_live_loop(args.scan_timeout))
    except KeyboardInterrupt:
        print("\n[!] Ingestion stopped.")
        if ENTROPY_BUFFER:
            _flush_seed(ENTROPY_BUFFER)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())