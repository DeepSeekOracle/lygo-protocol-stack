#!/usr/bin/env python3
"""LYGO BLE Mesh Bouncer — off-grid anchor hash discovery (scan + emulate broadcast)."""

from __future__ import annotations

import argparse
import asyncio
import json
import platform
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from lygo_anchor_config import AnchorProfile  # noqa: E402
from lygo_mesh_router import LygoMeshRouter  # noqa: E402

try:
    from bleak import BleakScanner

    BLEAK_OK = True
except ImportError:
    BLEAK_OK = False


class LygoBleMeshBouncer:
    def __init__(self, target_service_uuid: str = "0000180d-0000-1000-8000-00805f9b34fb"):
        self.profile = AnchorProfile.load()
        self.target_service_uuid = target_service_uuid
        self.seen_hashes: set[str] = set()
        self.router = LygoMeshRouter()

    def parse_manufacturer_data(self, manufacturer_data: dict) -> str:
        if not manufacturer_data:
            return ""
        for company_id, data_bytes in manufacturer_data.items():
            if int(company_id) == self.profile.ble_company_id:
                return data_bytes.hex()
        return ""

    async def run_discovery_and_bounce_loop(self, scan_duration: int = 10) -> dict:
        if not BLEAK_OK:
            return {"ok": False, "error": "bleak_not_installed", "hint": "pip install bleak"}

        new_records = 0

        def detection_callback(device, advertisement_data):
            nonlocal new_records
            raw_payload = self.parse_manufacturer_data(advertisement_data.manufacturer_data)
            if raw_payload and raw_payload not in self.seen_hashes:
                self.seen_hashes.add(raw_payload)
                if self.router.record(raw_payload, source=device.address, hop=1):
                    new_records += 1

        scanner = BleakScanner(detection_callback)
        await scanner.start()
        await asyncio.sleep(scan_duration)
        await scanner.stop()
        return {"ok": True, "new_records": new_records, "total_seen": len(self.seen_hashes)}

    async def broadcast_state_hash(self, state_hash_hex: str) -> dict:
        compressed = state_hash_hex[:16]
        if platform.system() != "Linux":
            self.router.record(compressed, source="local_emulation", hop=0)
            return {
                "ok": True,
                "mode": "emulation",
                "payload": compressed,
                "note": "Peripheral BLE advertising requires Linux BlueZ; stored locally for mesh router.",
            }
        return {"ok": False, "error": "linux_peripheral_not_implemented", "payload": compressed}


async def _main_async(scan: int, broadcast: str | None) -> int:
    bouncer = LygoBleMeshBouncer()
    out: dict = {}
    if broadcast:
        out["broadcast"] = await bouncer.broadcast_state_hash(broadcast)
    out["scan"] = await bouncer.run_discovery_and_bounce_loop(scan)
    print(json.dumps(out, indent=2))
    return 0 if out.get("scan", {}).get("ok", True) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan-seconds", type=int, default=5)
    ap.add_argument("--broadcast-hash", default="")
    args = ap.parse_args()
    bh = args.broadcast_hash or None
    return asyncio.run(_main_async(args.scan_seconds, bh))


if __name__ == "__main__":
    raise SystemExit(main())