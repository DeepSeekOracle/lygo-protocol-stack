#!/usr/bin/env python3
"""Legacy harness WebSocket (:8790) — delegates to ble_ws_broadcast_server."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.ble_ws_broadcast_server import run_server  # noqa: E402

DEFAULT_PORT = 8790


async def main(port: int = DEFAULT_PORT) -> None:
    await run_server("127.0.0.1", port)


if __name__ == "__main__":
    asyncio.run(main())