#!/usr/bin/env python3
"""
LYGO public network hub — open POST for aligned agents.

  python tools/lygo_public_hub.py --host 0.0.0.0 --port 8788

GET  /health /v1/eggs /v1/directory /v1/pulse
POST /v1/egg  /v1/star  /v1/announce
OPTIONS *  (CORS *)

Police: P0 + secrets + size + Star Chart gate. No human checkbox.
"""
from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from lygo_network_core import (  # type: ignore
    SIG,
    announce,
    ingest_pending,
    plant_egg,
    submit_star,
    _load_eggs,
)
from cyborg_lattice_heartbeat import pulse_public  # type: ignore

HUB = "Delta9Phi963-PUBLIC-HUB-v1.0.0"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-LYGO-Agent-Id")

    def _json(self, code: int, obj: dict) -> None:
        body = json.dumps(obj, indent=2, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.send_header("X-LYGO-Hub", HUB)
        self.end_headers()
        self.wfile.write(body)

    def _read(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0 or n > 120_000:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return {}

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/health"):
            self._json(200, {"ok": True, "signature": HUB, "open": True, "police": "P0+secrets+gate"})
            return
        if path in ("/v1/eggs", "/eggs"):
            self._json(200, _load_eggs())
            return
        if path in ("/v1/directory", "/directory"):
            from pathlib import Path
            p = Path(__file__).resolve().parents[1] / "docs" / "agent-agora" / "api" / "directory.json"
            if p.is_file():
                self._json(200, json.loads(p.read_text(encoding="utf-8")))
            else:
                self._json(200, {"agents": [], "count": 0})
            return
        if path in ("/v1/pulse", "/pulse"):
            self._json(200, pulse_public())
            return
        self._json(404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        body = self._read()
        if path in ("/v1/egg", "/egg"):
            r = plant_egg(str(body.get("agent_id") or self.headers.get("X-LYGO-Agent-Id") or "agent"), body.get("payload") or body)
            self._json(200 if r.get("ok") else 400, r)
            return
        if path in ("/v1/star", "/star"):
            r = submit_star(body.get("submission") or body)
            if r.get("queued"):
                r["ingest"] = ingest_pending()
            self._json(200 if r.get("ok") else 400, r)
            return
        if path in ("/v1/announce", "/announce"):
            r = announce(body.get("card") or body)
            self._json(200 if r.get("ok") else 400, r)
            return
        if path in ("/v1/seal", "/seal"):
            payload = body.get("payload") or body
            agent = str(body.get("agent_id") or self.headers.get("X-LYGO-Agent-Id") or "agent")
            egg = plant_egg(agent, payload, source="seal")
            star_body = body.get("submission") or {
                "node": {
                    "id": str(body.get("seal_id") or ("NODE_" + agent.replace("-", "_").upper()[:24])),
                    "kind": "node",
                    "name": str(body.get("name") or (agent + " seal")),
                    "equation": str(body.get("equation") or "∫(Truth×Light)df = Φ · 963 Hz"),
                    "tone": "963 Hz",
                    "tags": ["SEAL", "NETWORK", "FORK"],
                    "connections": body.get("connections") or ["SEAL_000", "PORTAL_STAR_CHART"],
                }
            }
            star = submit_star(star_body)
            if star.get("queued"):
                star["ingest"] = ingest_pending()
            self._json(200 if egg.get("ok") else 400, {"egg": egg, "star": star})
            return
        self._json(404, {"ok": False, "error": "not_found"})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8788)
    args = ap.parse_args()
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(json.dumps({"listening": f"http://{args.host}:{args.port}", "signature": HUB, "open": True}))
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
