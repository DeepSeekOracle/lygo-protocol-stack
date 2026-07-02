#!/usr/bin/env python3
"""Push live IBI / P0 seed to harness UI (optional websockets)."""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = Path(__file__).resolve().parent / "workspace"
SEED_JSON = WORKSPACE / "latest_seed.json"
DEFAULT_PORT = 8790


async def _handler(websocket) -> None:
    while True:
        try:
            payload = {"timestamp": time.time(), "seed": None, "seed_preview": None, "ibi_buffer": 0, "h_min": None}
            if SEED_JSON.is_file():
                data = json.loads(SEED_JSON.read_text(encoding="utf-8"))
                payload.update(
                    {
                        "seed": data.get("seed_256"),
                        "seed_preview": data.get("seed_preview") or str(data.get("seed_256", ""))[:16],
                        "h_min": data.get("h_min"),
                        "ibi_count": data.get("ibi_count"),
                        "source": data.get("signature"),
                    }
                )
            await websocket.send(json.dumps(payload))
            await asyncio.sleep(0.5)
        except Exception:
            break


async def main(port: int = DEFAULT_PORT) -> None:
    try:
        import websockets
    except ImportError:
        print("pip install websockets to run live harness feed", flush=True)
        raise SystemExit(1)

    async with websockets.serve(_handler, "127.0.0.1", port):
        print(f"LYGO harness WebSocket ws://127.0.0.1:{port}", flush=True)
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())