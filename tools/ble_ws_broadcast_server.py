#!/usr/bin/env python3
"""WebSocket broadcast for live BLE IBI + P0 seeds (Biophase7 Objective)."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from protocol7_human_ai_interface import live_stream_hub as hub  # noqa: E402

DEFAULT_PORT_OBJECTIVE = 8788
DEFAULT_PORT_HARNESS = 8790

_clients: set = set()
_event_queue: asyncio.Queue | None = None
_loop: asyncio.AbstractEventLoop | None = None


def schedule_broadcast(message: dict) -> None:
    """Thread-safe: called from bleak notification callback."""
    global _loop, _event_queue
    if _loop is None or _event_queue is None:
        return

    def _put() -> None:
        if _event_queue is not None:
            try:
                _event_queue.put_nowait(message)
            except asyncio.QueueFull:
                pass

    _loop.call_soon_threadsafe(_put)


async def _fan_out(message: dict) -> None:
    if not _clients:
        return
    raw = json.dumps(message)
    dead = []
    for ws in list(_clients):
        try:
            await ws.send(raw)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _clients.discard(ws)


async def _handler(websocket) -> None:
    _clients.add(websocket)
    try:
        await websocket.send(json.dumps({"type": "hello", "signature": hub.SIGNATURE, "snapshot": hub.snapshot()}))
        await websocket.wait_closed()
    finally:
        _clients.discard(websocket)


async def _pump_events() -> None:
    assert _event_queue is not None
    while True:
        msg = await _event_queue.get()
        await _fan_out(msg)


async def _heartbeat() -> None:
    while True:
        snap = hub.snapshot()
        if snap.get("ibi_history") or snap.get("seed_256"):
            await _fan_out({"type": "snapshot", **snap})
        await asyncio.sleep(0.5)


async def run_server(host: str, port: int) -> None:
    global _event_queue, _loop
    try:
        import websockets
    except ImportError:
        print("pip install websockets (see requirements-p7-ble.txt)", file=sys.stderr)
        raise SystemExit(1)

    _loop = asyncio.get_running_loop()
    _event_queue = asyncio.Queue(maxsize=512)
    asyncio.create_task(_pump_events())
    asyncio.create_task(_heartbeat())

    async with websockets.serve(_handler, host, port):
        print(f"LYGO BLE WebSocket ws://{host}:{port} ({hub.SIGNATURE})", flush=True)
        await asyncio.Future()


def main() -> int:
    ap = argparse.ArgumentParser(description="Broadcast live BLE stream over WebSocket")
    ap.add_argument("--host", default="0.0.0.0", help="Bind address (0.0.0.0 for Cloudflare/ngrok tunnel)")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT_OBJECTIVE)
    ap.add_argument("--harness", action="store_true", help=f"Use harness port {DEFAULT_PORT_HARNESS} on 127.0.0.1")
    args = ap.parse_args()
    host = "127.0.0.1" if args.harness else args.host
    port = DEFAULT_PORT_HARNESS if args.harness else args.port
    asyncio.run(run_server(host, port))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())