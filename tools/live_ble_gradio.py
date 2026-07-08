"""
HF Space / Gradio live BLE consumer — connects to operator tunnel (not localhost on cloud).
Set LYGO_BLE_WS_URL=wss://your-tunnel.example/ws or pass URL in UI.
"""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Any

_lock = threading.Lock()
_state: dict[str, Any] = {
    "connected": False,
    "last_error": "",
    "latest_ibi_ms": 0,
    "buffer_size": 0,
    "h_min": 0.0,
    "seed": "",
    "ibi_history": [],
    "ws_url": "",
}

_ws_thread: threading.Thread | None = None
_ws_stop = threading.Event()


def _apply_message(data: dict) -> None:
    global _state
    with _lock:
        if data.get("type") == "ibi":
            ibi = int(data.get("ibi_ms") or 0)
            if ibi > 0:
                _state["latest_ibi_ms"] = ibi
                hist = list(_state.get("ibi_history") or [])
                hist.append(ibi)
                _state["ibi_history"] = hist[-100:]
            _state["buffer_size"] = int(data.get("buffer_size") or _state.get("buffer_size") or 0)
            if data.get("h_min") is not None:
                _state["h_min"] = float(data["h_min"])
        elif data.get("type") == "seed":
            _state["seed"] = str(data.get("seed") or data.get("seed_256") or "")
            if data.get("h_min") is not None:
                _state["h_min"] = float(data["h_min"])
            _state["buffer_size"] = 0
        elif data.get("type") in ("snapshot", "hello"):
            if data.get("latest_ibi_ms"):
                _state["latest_ibi_ms"] = int(data["latest_ibi_ms"])
            if data.get("ibi_history"):
                _state["ibi_history"] = list(data["ibi_history"])[-100:]
            if data.get("buffer_size") is not None:
                _state["buffer_size"] = int(data["buffer_size"])
            if data.get("h_min") is not None:
                _state["h_min"] = float(data["h_min"])
            if data.get("seed_256"):
                _state["seed"] = str(data["seed_256"])


def _ws_loop(url: str) -> None:
    try:
        import websocket  # websocket-client
    except ImportError:
        with _lock:
            _state["last_error"] = "pip install websocket-client"
            _state["connected"] = False
        return

    def on_message(_ws, message: str) -> None:
        try:
            _apply_message(json.loads(message))
        except json.JSONDecodeError:
            pass

    def on_open(_ws) -> None:
        with _lock:
            _state["connected"] = True
            _state["last_error"] = ""

    def on_error(_ws, err) -> None:
        with _lock:
            _state["connected"] = False
            _state["last_error"] = str(err)[:200]

    def on_close(_ws, *_args) -> None:
        with _lock:
            _state["connected"] = False

    while not _ws_stop.is_set():
        app = websocket.WebSocketApp(url, on_message=on_message, on_open=on_open, on_error=on_error, on_close=on_close)
        app.run_forever(ping_interval=20, ping_timeout=10)
        if _ws_stop.is_set():
            break
        time.sleep(2.0)


def connect_ws(url: str) -> str:
    global _ws_thread
    url = (url or "").strip()
    if not url:
        url = os.environ.get("LYGO_BLE_WS_URL", "").strip()
    if not url:
        return "Set **LYGO_BLE_WS_URL** (Space secret) or paste your `wss://` tunnel URL."
    if url.startswith("https://"):
        url = "wss://" + url[len("https://") :]
    if url.startswith("http://"):
        url = "ws://" + url[len("http://") :]

    _ws_stop.set()
    if _ws_thread and _ws_thread.is_alive():
        _ws_thread.join(timeout=2.0)
    _ws_stop.clear()
    with _lock:
        _state["ws_url"] = url
    _ws_thread = threading.Thread(target=_ws_loop, args=(url,), daemon=True)
    _ws_thread.start()
    return f"Connecting to `{url}` (tunnel → local :8788)…"


def disconnect_ws() -> str:
    _ws_stop.set()
    with _lock:
        _state["connected"] = False
    return "Disconnected."


def refresh_dashboard() -> tuple:
    """Returns Gradio outputs: ibi, buffer, h_min, seed, lineplot df, hist list, status md."""
    import pandas as pd

    with _lock:
        st = dict(_state)
    hist = st.get("ibi_history") or []
    seed = st.get("seed") or ""
    if not seed:
        seed = "Awaiting 64 IBIs…"
    status = (
        f"**WS:** `{'connected' if st.get('connected') else 'disconnected'}` · "
        f"**URL:** `{st.get('ws_url') or '—'}`"
    )
    if st.get("last_error"):
        status += f"\n\nError: `{st['last_error']}`"
    if not st.get("ws_url"):
        status += (
            "\n\nCloud HF cannot use `localhost`. Expose local ingest with **Cloudflare Tunnel** or **ngrok** "
            "to port **8788**, then set `LYGO_BLE_WS_URL`."
        )
    wave = hist[-50:] if hist else [0]
    df = pd.DataFrame({"time": list(range(len(wave))), "ibi": wave})
    return (
        float(st.get("latest_ibi_ms") or 0),
        int(st.get("buffer_size") or 0),
        float(st.get("h_min") or 0.0),
        seed,
        df,
        wave,
        status,
    )


def load_local_snapshot_from_file(path: str) -> str:
    """Fallback: read latest_seed.json from synced workspace (no live WS)."""
    from pathlib import Path

    p = Path(path)
    if not p.is_file():
        return "No local seed file."
    data = json.loads(p.read_text(encoding="utf-8"))
    _apply_message({"type": "seed", "seed": data.get("seed_256"), "h_min": data.get("h_min")})
    return f"Loaded seed preview `{str(data.get('seed_preview', ''))[:16]}` from file."