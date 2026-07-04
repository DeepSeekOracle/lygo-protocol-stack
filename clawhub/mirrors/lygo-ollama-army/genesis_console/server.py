#!/usr/bin/env python3
"""LYGO Genesis Console v3 — unified LYGO monitor (GitHub, HF, lattice, Joy, army)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
COLLECTOR = ROOT / "collector.py"
DATA = ROOT / "data" / "status.json"
PORT = int(os.environ.get("LYGO_GENESIS_PORT", "9963"))
REFRESH_SEC = int(os.environ.get("LYGO_GENESIS_REFRESH", "120"))
JOY_PORT = int(os.environ.get("LYGO_JOY_API_PORT", "9965"))

_collector_lock = threading.Lock()


def run_collector() -> None:
    with _collector_lock:
        subprocess.run(
            [sys.executable, str(COLLECTOR)],
            cwd=str(ROOT),
            timeout=300,
            check=False,
        )


def collector_loop() -> None:
    while True:
        try:
            run_collector()
        except Exception as exc:
            print(f"[collector] {exc}")
        time.sleep(REFRESH_SEC)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send_json(self, body: str, code: int = 200) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/status":
            if not DATA.is_file():
                run_collector()
            body = DATA.read_text(encoding="utf-8") if DATA.is_file() else "{}"
            self._send_json(body)
            return
        if path == "/api/refresh":
            run_collector()
            body = DATA.read_text(encoding="utf-8") if DATA.is_file() else "{}"
            self._send_json(body)
            return
        if path == "/api/joy-proxy":
            try:
                import urllib.request

                req = urllib.request.Request(
                    f"http://127.0.0.1:{JOY_PORT}/api/joy",
                    headers={"User-Agent": "LYGO-Genesis-Console/3.0"},
                )
                with urllib.request.urlopen(req, timeout=3) as resp:
                    self._send_json(resp.read().decode())
            except Exception as exc:
                self._send_json(json.dumps({"ok": False, "error": str(exc)}), code=503)
            return
        if path in ("/", "/index.html"):
            path = "/index.html"
        file_path = STATIC / path.lstrip("/")
        if not file_path.is_file() or not str(file_path.resolve()).startswith(str(STATIC.resolve())):
            self.send_error(404)
            return
        content = file_path.read_bytes()
        ctype = "text/html" if file_path.suffix == ".html" else "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(content)


def main() -> int:
    run_collector()
    threading.Thread(target=collector_loop, daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/"
    print(f"LYGO Genesis Console v3 → {url}")
    print(f"Joy Architect (if running) → http://127.0.0.1:{JOY_PORT}/architect")
    print(f"Background sync every {REFRESH_SEC}s")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Genesis Console stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())