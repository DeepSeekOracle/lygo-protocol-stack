#!/usr/bin/env python3
"""
Standalone LYGO Agent Lattice hub (Layer E).

Secure presence directory for LYGO-aligned agents. Can run alone or alongside
node_api_server. Defaults to port 8791.

Endpoints:
  GET  /health
  GET  /agent/directory
  GET  /agent/{agent_id}
  POST /agent/announce
  POST /agent/gossip
  GET  /badge  (living mesh if available)

Env:
  LYGO_AGENT_HUB_TOKEN  optional shared secret (header X-LYGO-Agent-Token)
  LYGO_STACK_ROOT       optional
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from agent_lattice_core import (  # noqa: E402
    AgentDirectory,
    SIG,
    build_agent_card,
    validate_card,
)

HUB_SIG = "Delta9Phi963-AGENT-LATTICE-HUB-v1"


class HubHandler(BaseHTTPRequestHandler):
    directory = AgentDirectory()
    require_token = False
    hub_token = ""

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _json(self, code: int, obj: dict) -> None:
        body = json.dumps(obj, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-LYGO-Hub", HUB_SIG)
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0 or n > 64_000:
            return {}
        raw = self.rfile.read(n)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def _auth_ok(self) -> bool:
        if not self.require_token:
            return True
        tok = self.headers.get("X-LYGO-Agent-Token") or ""
        return bool(self.hub_token) and tok == self.hub_token

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            self._json(
                200,
                {
                    "ok": True,
                    "service": "lygo-agent-lattice-hub",
                    "signature": HUB_SIG,
                    "protocol": SIG,
                    "agent_count": len(self.directory.list_cards()),
                },
            )
            return
        if path in ("/agent/directory", "/agent/lattice"):
            self._json(200, self.directory.snapshot())
            return
        if path.startswith("/agent/") and path not in ("/agent/announce", "/agent/gossip"):
            aid = path[len("/agent/") :].strip("/")
            if aid and aid not in ("directory", "lattice", "announce", "gossip"):
                for c in self.directory.list_cards():
                    if c.get("agent_id") == aid:
                        self._json(200, {"agent_id": aid, "card": c})
                        return
                self._json(404, {"error": "unknown_agent", "agent_id": aid})
                return
        if path in ("/badge", "/badge/living"):
            try:
                from collect_living_mesh_badge import collect_living_badge

                self._json(200, collect_living_badge(quick=True))
            except Exception as e:
                self._json(200, build_agent_card())
            return
        self._json(
            404,
            {
                "error": "not found",
                "paths": [
                    "/health",
                    "/agent/directory",
                    "/agent/{agent_id}",
                    "POST /agent/announce",
                    "POST /agent/gossip",
                    "/badge",
                ],
            },
        )

    def do_POST(self) -> None:
        if not self._auth_ok():
            self._json(401, {"error": "unauthorized", "hint": "X-LYGO-Agent-Token"})
            return
        path = urlparse(self.path).path
        body = self._read_json()
        if path == "/agent/announce":
            card = body.get("card") or body
            if not isinstance(card, dict):
                self._json(400, {"error": "bad_card"})
                return
            errs = validate_card(card, require_aligned=False)
            # soft: still reject secrets / quarantine / size
            hard = [e for e in errs if e in ("secret_pattern", "card_too_large", "quarantine_card", "bad_agent_id", "agent_id_charset", "bad_signature")]
            if hard:
                self._json(400, {"ok": False, "errors": hard})
                return
            if "expired" in errs:
                self._json(400, {"ok": False, "errors": ["expired"]})
                return
            result = self.directory.upsert(card, source="announce")
            code = 200 if result.get("ok") else 429 if "rate_limited" in (result.get("errors") or []) else 400
            self._json(code, {**result, "signature": HUB_SIG})
            return
        if path == "/agent/gossip":
            cards = body.get("cards") or body.get("agents") or []
            if isinstance(cards, dict):
                cards = list(cards.values())
            merged = 0
            rejected = 0
            for item in cards:
                c = item.get("card") if isinstance(item, dict) and "card" in item else item
                if not isinstance(c, dict):
                    rejected += 1
                    continue
                r = self.directory.upsert(c, source="gossip")
                if r.get("ok"):
                    merged += 1
                else:
                    rejected += 1
            # also accept single card
            if body.get("card"):
                r = self.directory.upsert(body["card"], source="gossip")
                if r.get("ok"):
                    merged += 1
            self._json(
                200,
                {
                    "ok": True,
                    "merged": merged,
                    "rejected": rejected,
                    "directory": self.directory.snapshot(),
                    "signature": HUB_SIG,
                },
            )
            return
        self._json(404, {"error": "not found"})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8791)
    ap.add_argument("--require-token", action="store_true")
    args = ap.parse_args()

    HubHandler.hub_token = os.environ.get("LYGO_AGENT_HUB_TOKEN", "")
    HubHandler.require_token = args.require_token or bool(HubHandler.hub_token)
    # if token set, require it; if empty and not --require-token, open local hub
    if args.require_token and not HubHandler.hub_token:
        print("ERROR: --require-token needs LYGO_AGENT_HUB_TOKEN", file=sys.stderr)
        return 2
    if not args.require_token and not HubHandler.hub_token:
        HubHandler.require_token = False

    server = ThreadingHTTPServer((args.host, args.port), HubHandler)
    print(f"LYGO Agent Lattice hub on http://{args.host}:{args.port} ({HUB_SIG})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutdown")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
