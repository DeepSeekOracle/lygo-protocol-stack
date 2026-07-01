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
    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return {}

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
            self._json(200, {"ok": True, "service": "lygo-node", "signature": "Δ9Φ963-PHASE3-SCALE-INIT"})
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
        if path == "/gossip":
            snap = get_stack().federation.snapshot()
            recent = snap.get("gossip_recent") or []
            self._json(
                200,
                {
                    "peers": snap.get("peers", []),
                    "badge_count": len(recent),
                    "gossip_recent": recent,
                    "local_node_id": snap.get("local_node_id"),
                    "signature": "Δ9Φ963-PHASE5-MESH-GOSSIP-v1",
                },
            )
            return
        if path.startswith("/badge/"):
            node_id = path.split("/")[-1]
            snap = get_stack().federation.snapshot()
            for entry in reversed(snap.get("gossip_recent") or []):
                if str(entry.get("node_id")) == node_id:
                    self._json(200, entry.get("badge") or entry)
                    return
            self._json(404, {"error": "node badge not in gossip log", "node_id": node_id})
            return
        self._json(
            404,
            {
                "error": "not found",
                "paths": [
                    "/health",
                    "/badge",
                    "/badge/{node_id}",
                    "/demo",
                    "/elasticity",
                    "/federation",
                    "/gossip",
                    "POST /gossip/badge",
                    "POST /gossip/scatter",
                ],
            },
        )

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/gossip/badge":
            body = self._read_json_body()
            badge = body.get("badge") or body
            from_node = body.get("from") or badge.get("node_id") or "remote"
            stack = get_stack()
            msg = stack.federation.gossip.publish_badge(str(from_node), badge if isinstance(badge, dict) else {"raw": badge})
            self._json(200, {"ok": True, "signature": "Δ9Φ963-PHASE5-MESH-GOSSIP-v1", "gossip": msg})
            return
        if path == "/gossip/scatter":
            body = self._read_json_body()
            stack = get_stack()
            merged = 0
            if isinstance(body, dict):
                for node_id, badge in body.items():
                    if isinstance(badge, dict):
                        stack.federation.gossip.publish_badge(str(node_id), badge)
                        merged += 1
            self._json(200, {"ok": True, "merged": merged, "signature": "Δ9Φ963-PHASE5-MESH-SCATTER-v1"})
            return
        self._json(404, {"error": "not found"})

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