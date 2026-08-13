#!/usr/bin/env python3
"""LYGO Genesis Console v3 — unified LYGO monitor (local HTTP only). SkillSpector-safe."""

from __future__ import annotations

import json
import os
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
SKILL = ROOT.parent
sys.path.insert(0, str(SKILL))
from _safe_invoke import run_python  # noqa: E402

STATIC = ROOT / "static"
COLLECTOR = ROOT / "collector.py"
DATA = ROOT / "data" / "status.json"
PORT = int(os.environ.get("LYGO_GENESIS_PORT", "9963"))
REFRESH_SEC = int(os.environ.get("LYGO_GENESIS_REFRESH", "120"))
JOY_PORT = int(os.environ.get("LYGO_JOY_API_PORT", "9965"))

_collector_lock = threading.Lock()


def run_collector() -> None:
    with _collector_lock:
        run_python(COLLECTOR, cwd=ROOT, timeout=300)


def collector_loop() -> None:
    while True:
        try:
            run_collector()
        except Exception as exc:
            print(f"[collector] {exc}")
        time.sleep(REFRESH_SEC)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            body = (STATIC / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path in ("/api/status", "/status.json"):
            if not DATA.is_file():
                run_collector()
            raw = DATA.read_bytes() if DATA.is_file() else b"{}"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if path == "/api/refresh":
            run_collector()
            self.send_response(204)
            self.end_headers()
            return
        self.send_error(404)


def main() -> int:
    """Localhost-only dashboard. Optional browser open is OFF by default (SkillSpector)."""
    DATA.parent.mkdir(parents=True, exist_ok=True)
    threading.Thread(target=collector_loop, name="genesis-collector", daemon=True).start()
    run_collector()
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/"
    print(f"Genesis console on {url} (localhost only — not public)")
    print("  bind: 127.0.0.1 only · no remote clients · no auth (local operator trust)")
    open_browser = os.environ.get("LYGO_GENESIS_OPEN_BROWSER", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    if open_browser:
        try:
            webbrowser.open(url)
            print("  browser: opened (LYGO_GENESIS_OPEN_BROWSER=1)")
        except Exception as exc:
            print(f"  browser: open failed ({exc})")
    else:
        print("  browser: not opened (set LYGO_GENESIS_OPEN_BROWSER=1 to auto-open)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("shutdown")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
