"""Thread-safe live IBI / P0 seed state for BLE ingest, WebSocket, and HF UI."""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any

SIGNATURE = "Δ9Φ963-PHASE7-LIVE-STREAM-v1"

_lock = threading.Lock()
_ibi_history: deque[int] = deque(maxlen=128)
_buffer_size = 0
_latest_ibi = 0
_latest_seed = ""
_latest_h_min: float | None = None
_latest_seed_preview = ""
_connected_source = "idle"


def reset(source: str = "idle") -> None:
    global _buffer_size, _latest_ibi, _latest_seed, _latest_h_min, _latest_seed_preview, _connected_source
    with _lock:
        _ibi_history.clear()
        _buffer_size = 0
        _latest_ibi = 0
        _latest_seed = ""
        _latest_h_min = None
        _latest_seed_preview = ""
        _connected_source = source


def record_ibi(ibi_ms: int, buffer_size: int, *, h_min: float | None = None, source: str = "ble") -> dict[str, Any]:
    global _buffer_size, _latest_ibi, _latest_h_min, _connected_source
    with _lock:
        _ibi_history.append(int(ibi_ms))
        _buffer_size = int(buffer_size)
        _latest_ibi = int(ibi_ms)
        if h_min is not None:
            _latest_h_min = float(h_min)
        _connected_source = source
        return _snapshot_unlocked()


def record_seed(
    seed_256: str,
    *,
    h_min: float | None,
    ibi_count: int,
    source: str = "ble",
) -> dict[str, Any]:
    global _latest_seed, _latest_h_min, _latest_seed_preview, _buffer_size, _connected_source
    with _lock:
        _latest_seed = str(seed_256)
        _latest_seed_preview = _latest_seed[:16]
        if h_min is not None:
            _latest_h_min = float(h_min)
        _buffer_size = 0
        _connected_source = source
        return _snapshot_unlocked(ibi_count=ibi_count)


def _snapshot_unlocked(ibi_count: int | None = None) -> dict[str, Any]:
    hist = list(_ibi_history)
    return {
        "signature": SIGNATURE,
        "timestamp": time.time(),
        "source": _connected_source,
        "latest_ibi_ms": _latest_ibi,
        "buffer_size": _buffer_size,
        "ibi_count": ibi_count if ibi_count is not None else len(hist),
        "h_min": _latest_h_min,
        "seed_256": _latest_seed or None,
        "seed_preview": _latest_seed_preview or None,
        "ibi_history": hist[-100:],
    }


def snapshot() -> dict[str, Any]:
    with _lock:
        return _snapshot_unlocked()


def ws_message_ibi(ibi_ms: int, buffer_size: int, *, h_min: float | None = None) -> dict[str, Any]:
    msg: dict[str, Any] = {
        "type": "ibi",
        "signature": SIGNATURE,
        "timestamp": time.time(),
        "ibi_ms": int(ibi_ms),
        "buffer_size": int(buffer_size),
    }
    if h_min is not None:
        msg["h_min"] = float(h_min)
    return msg


def ws_message_seed(seed_256: str, *, h_min: float | None, ibi_count: int) -> dict[str, Any]:
    msg: dict[str, Any] = {
        "type": "seed",
        "signature": SIGNATURE,
        "timestamp": time.time(),
        "seed": str(seed_256),
        "seed_preview": str(seed_256)[:16],
        "ibi_count": int(ibi_count),
    }
    if h_min is not None:
        msg["h_min"] = float(h_min)
    return msg