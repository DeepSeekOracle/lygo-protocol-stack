#!/usr/bin/env python3
"""Minimal HTTP API for Dockerized LYGO community nodes."""

from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def _stack():
    import sys

    sys.path.insert(0, str(ROOT / "stack"))
    for sub in (
        "protocol0_nano_kernel/src/python",
        "protocol1_memory_mycelium/src/python",
        "protocol2_cognitive_bridge/src/python",
        "protocol3_vortex_consensus/src/python",
        "protocol4_ascension_engine/src/python",
        "protocol5_harmony_node/src/python",
    ):
        p = ROOT / sub
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    from lygo_stack import deploy_stack  # noqa: E402

    return deploy_stack(os.environ.get("LYGO_NODE_ID", "DOCKER_NODE"))


_STACK = None


def get_stack():
    global _STACK
    if _STACK is None:
        _STACK = _stack()
    return _STACK


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, obj: dict) -> None:
        body = json.dumps(obj, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/health"):
            self._json(200, {"ok": True, "service": "lygo-node", "signature": "Δ9Φ963-PHASE2-DEPLOYMENT"})
            return
        if path == "/badge":
            import sys

            tools = ROOT / "tools"
            if str(tools) not in sys.path:
                sys.path.insert(0, str(tools))
            from verify_alignment_badge import collect_badge  # noqa: E402

            badge = collect_badge(quick=True)
            self._json(200, badge)
            return
        if path == "/demo":
            demo = get_stack().demo_cycle()
            self._json(200, {"stack_version": get_stack().version, "p0_verdict": demo["p0"].get("verdict")})
            return
        if path == "/elasticity":
            st = get_stack().elasticity.status()
            self._json(200, st)
            return
        if path == "/federation":
            self._json(200, get_stack().federation.snapshot())
            return
        self._json(404, {"error": "not found", "paths": ["/health", "/badge", "/demo", "/elasticity", "/federation"]})

    def log_message(self, fmt: str, *args) -> None:
        return


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8787)
    args = ap.parse_args()
    srv = HTTPServer((args.host, args.port), Handler)
    print(f"LYGO node API on http://{args.host}:{args.port}")
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())