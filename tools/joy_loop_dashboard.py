#!/usr/bin/env python3
"""Joy Loop web dashboard — dance floor visualizer (replaces terminal-only show)."""

from __future__ import annotations

import json
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, Tuple
from urllib.parse import urlparse

if TYPE_CHECKING:
    from joy_loop_protocol import JoyLoopRuntime

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "docs" / "joy_loop" / "dashboard"
DEFAULT_PORT = int(os.environ.get("LYGO_JOY_DASHBOARD_PORT", "9964"))


def start_dashboard_server(
    runtime: "JoyLoopRuntime", *, port: int = DEFAULT_PORT, open_browser: bool = True
) -> Tuple[ThreadingHTTPServer, str]:
    url = f"http://127.0.0.1:{port}/"

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/api/joy":
                body = json.dumps(runtime.api_payload(), ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return
            if path in ("/", "/index.html"):
                rel = "index.html"
            else:
                rel = path.lstrip("/")
            file_path = (STATIC / rel).resolve()
            if not str(file_path).startswith(str(STATIC.resolve())) or not file_path.is_file():
                self.send_error(404)
                return
            data = file_path.read_bytes()
            ctype = "text/html; charset=utf-8" if file_path.suffix == ".html" else "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.end_headers()
            self.wfile.write(data)

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    return server, url


def main() -> int:
    import sys

    sys.path.insert(0, str(ROOT / "tools"))
    from joy_loop_protocol import JoyLoopRuntime

    rt = JoyLoopRuntime.get()
    if not rt.engine.states:
        print("no champions")
        return 1
    rt.start()
    server, url = start_dashboard_server(rt, open_browser=True)
    print(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        rt.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())