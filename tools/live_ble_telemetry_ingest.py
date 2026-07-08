#!/usr/bin/env python3
"""
LYGO Phase 7 — Live BLE telemetry ingest (GATT 0x180D) + optional WebSocket broadcast.
Biophase7 Objective: ws://0.0.0.0:8788 for tunnel → HF Space (LYGO_BLE_WS_URL).
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
from protocol7_human_ai_interface import live_stream_hub as hub  # noqa: E402

ENTROPY_BUFFER: list[int] = []


def _preview_h_min(ibi: list[int]) -> float | None:
    if len(ibi) < 4:
        return None
    pack = extract_p0_seed_from_ibi([float(x) for x in ibi[-min(32, len(ibi)) :]])
    return pack.get("h_min")


def _flush_seed(ibi: list[int], *, source: str = "ble") -> dict:
    pack = extract_p0_seed_from_ibi([float(x) for x in ibi])
    seed = str(pack.get("seed_256", ""))
    h_min = pack.get("h_min")
    payload = {
        "timestamp": time.time(),
        "signature": "Δ9Φ963-PHASE7-BLE-LIVE-HARNESS",
        "ibi_count": len(ibi),
        "h_min": h_min,
        "seed_256": seed,
        "seed_preview": seed[:16],
    }
    SEED_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    hub.record_seed(seed, h_min=h_min, ibi_count=len(ibi), source=source)
    try:
        from tools.ble_ws_broadcast_server import schedule_broadcast

        schedule_broadcast(hub.ws_message_seed(seed, h_min=h_min, ibi_count=len(ibi)))
    except Exception:
        pass
    return payload


def handle_notification(data: bytes, *, source: str = "ble") -> None:
    global ENTROPY_BUFFER
    parsed = parse_heart_rate_measurement(data)
    for ibi in parsed.get("ibi_ms") or []:
        ENTROPY_BUFFER.append(int(ibi))
        h_est = _preview_h_min(ENTROPY_BUFFER)
        hub.record_ibi(int(ibi), len(ENTROPY_BUFFER), h_min=h_est, source=source)
        try:
            from tools.ble_ws_broadcast_server import schedule_broadcast

            schedule_broadcast(hub.ws_message_ibi(int(ibi), len(ENTROPY_BUFFER), h_min=h_est))
        except Exception:
            pass
        print(f"[+] IBI: {ibi}ms | buffer {len(ENTROPY_BUFFER)}/{BUFFER_THRESHOLD}")
    if len(ENTROPY_BUFFER) >= BUFFER_THRESHOLD:
        print("[!] Threshold reached — extracting P0 seed...")
        out = _flush_seed(ENTROPY_BUFFER.copy(), source=source)
        print(f"[>] H_min={out['h_min']} seed={out['seed_preview']}…")
        ENTROPY_BUFFER.clear()


async def _live_loop(scan_timeout: float = 8.0) -> int:
    from bleak import BleakClient, BleakScanner

    print("=" * 70)
    print("LYGO PHASE 7 — LIVE BLE TELEMETRY INGEST")
    print("Δ9Φ963-PHASE7-BLE-LIVE-HARNESS")
    print("=" * 70)
    hub.reset("ble")
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


async def _simulate_stream(interval: float = 0.35, count: int = 80) -> None:
    """Emit synthetic IBI over WebSocket for HF/tunnel verification without hardware."""
    import random

    hub.reset("simulate")
    rng = random.Random(528963)
    for _ in range(count):
        ibi = int(60000 / 75 + rng.uniform(-40, 40))
        handle_notification(_fake_hr_pdu(ibi), source="simulate")
        await asyncio.sleep(interval)


def _fake_hr_pdu(ibi_ms: int) -> bytes:
    """Minimal GATT 0x2A37 PDU with one RR interval."""
    rr = int((ibi_ms / 1000.0) * 1024)
    hr = max(40, min(180, int(60000 / max(ibi_ms, 300))))
    return bytes([0x10, hr, rr & 0xFF, (rr >> 8) & 0xFF])


def run_simulated_flush(n: int = 64) -> dict:
    import random

    rng = random.Random(528963)
    ibi = [int(60000 / 75 + rng.uniform(-40, 40)) for _ in range(n)]
    hub.reset("simulate")
    return _flush_seed(ibi, source="simulate")


async def _run_with_ws(
    *,
    host: str,
    port: int,
    simulate_stream: bool,
    scan_timeout: float,
) -> int:
    from tools.ble_ws_broadcast_server import run_server

    server_task = asyncio.create_task(run_server(host, port))
    await asyncio.sleep(0.3)
    if simulate_stream:
        await _simulate_stream()
        print("[*] Synthetic stream complete — WebSocket still listening (Ctrl+C to exit)")
        try:
            await server_task
        except asyncio.CancelledError:
            pass
        return 0
    code = await _live_loop(scan_timeout)
    server_task.cancel()
    return code


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--simulate", action="store_true", help="Write seed from synthetic IBI (no BLE)")
    ap.add_argument("--with-ws", action="store_true", help="Run WebSocket broadcast alongside ingest")
    ap.add_argument("--ws-host", default="0.0.0.0")
    ap.add_argument("--ws-port", type=int, default=8788)
    ap.add_argument("--simulate-stream", action="store_true", help="With --with-ws: stream synthetic IBI over WS")
    ap.add_argument("--scan-timeout", type=float, default=8.0)
    args = ap.parse_args()

    if args.simulate:
        out = run_simulated_flush()
        print(json.dumps(out, indent=2))
        return 0

    if args.with_ws:
        if args.simulate_stream:
            try:
                return asyncio.run(
                    _run_with_ws(
                        host=args.ws_host, port=args.ws_port, simulate_stream=True, scan_timeout=args.scan_timeout
                    )
                )
            except KeyboardInterrupt:
                return 0
        if not bleak_available() and not args.simulate_stream:
            print("bleak not installed — pip install bleak  OR  --simulate-stream", file=sys.stderr)
            return 1
        try:
            return asyncio.run(
                _run_with_ws(host=args.ws_host, port=args.ws_port, simulate_stream=False, scan_timeout=args.scan_timeout)
            )
        except KeyboardInterrupt:
            print("\n[!] Ingestion stopped.")
            if ENTROPY_BUFFER:
                _flush_seed(ENTROPY_BUFFER)
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