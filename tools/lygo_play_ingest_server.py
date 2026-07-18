#!/usr/bin/env python3
"""
LYGO Play Lattice ingest server (CORS) — multi-listener play events.

  python tools/lygo_play_ingest_server.py --host 127.0.0.1 --port 8777
  # public (careful): --host 0.0.0.0 --port 8777

API:
  GET  /v1/health
  GET  /v1/counts          → play_counts aggregate (no increment)
  GET  /v1/merkle
  POST /v1/play            → body: play event JSON (hash-chained)
  POST /v1/play/batch      → {events:[...]}

Pairs with listen portal client. Optional --publish-every N to push HF.
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

STACK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STACK / "tools"))

import lygo_play_lattice as L  # noqa: E402


class State:
    publish_every = 0
    since_publish = 0
    lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[play-ingest]", fmt % args, flush=True)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")

    def _json(self, code: int, obj: dict):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = unquote(self.path.split("?", 1)[0])
        if path in ("/", "/v1/health"):
            return self._json(
                200,
                {
                    "ok": True,
                    "signature": L.SIGNATURE_LATTICE,
                    "service": "lygo-play-ingest",
                    "endpoints": ["/v1/counts", "/v1/merkle", "/v1/play"],
                },
            )
        if path == "/v1/counts":
            if not L.AGGREGATE.exists():
                L.rebuild_aggregate()
            agg = json.loads(L.AGGREGATE.read_text(encoding="utf-8"))
            return self._json(200, agg)
        if path == "/v1/merkle":
            if L.MERKLE.exists():
                return self._json(200, {"merkle_root": L.MERKLE.read_text(encoding="utf-8").strip()})
            return self._json(404, {"error": "no merkle yet"})
        return self._json(404, {"error": "not found"})

    def do_POST(self):
        path = unquote(self.path.split("?", 1)[0])
        n = int(self.headers.get("Content-Length") or 0)
        if n > 200_000:
            return self._json(413, {"error": "payload too large"})
        raw = self.rfile.read(n) if n else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return self._json(400, {"error": "invalid json"})

        if path == "/v1/play":
            ev = data.get("event") if "event" in data else data
            # fill defaults for browser partials
            if isinstance(ev, dict):
                if not ev.get("event_id"):
                    import uuid

                    ev["event_id"] = str(uuid.uuid4())
                if not ev.get("ts"):
                    ev["ts"] = L.utc_now()
                if not ev.get("signature"):
                    ev["signature"] = L.SIGNATURE_EVENT
                if not ev.get("v"):
                    ev["v"] = 1
                if not ev.get("prev_hash"):
                    ev["prev_hash"] = L.last_event_hash(L.load_events())
                if not ev.get("client_id"):
                    ev["client_id"] = "anonymous-web"
                # always recompute server-side hash over server-normalized fields
                # keep client event_hash if valid; else recompute
                try:
                    if not ev.get("event_hash") or L.compute_event_hash(ev) != ev.get("event_hash"):
                        # strip bad hash and recompute
                        ev.pop("event_hash", None)
                        ev["event_hash"] = L.compute_event_hash(ev)
                except Exception:
                    ev["event_hash"] = L.compute_event_hash(ev)

            ok, msg = L.append_event(ev if isinstance(ev, dict) else {})
            if not ok and msg not in ("duplicate event_id", "duplicate event_hash"):
                return self._json(400, {"ok": False, "error": msg})
            with State.lock:
                if ok:
                    State.since_publish += 1
                agg = L.rebuild_aggregate()
                if State.publish_every and State.since_publish >= State.publish_every:
                    try:
                        L.publish_hf()
                        State.since_publish = 0
                    except Exception as e:
                        print("[play-ingest] hf publish defer:", e, flush=True)
            return self._json(
                200,
                {
                    "ok": True,
                    "accepted": ok,
                    "message": msg,
                    "total_plays": agg.get("total_plays"),
                    "track_plays": (agg.get("by_track") or {}).get(
                        (ev.get("track_sha256") or "").lower()
                    )
                    if isinstance(ev, dict)
                    else None,
                    "merkle_root": agg.get("merkle_root"),
                },
            )

        if path == "/v1/play/batch":
            events = data.get("events") or []
            accepted = 0
            for ev in events[:200]:
                if not isinstance(ev, dict):
                    continue
                if not ev.get("event_hash"):
                    if not ev.get("prev_hash"):
                        ev["prev_hash"] = L.last_event_hash(L.load_events())
                    if not ev.get("event_id"):
                        import uuid

                        ev["event_id"] = str(uuid.uuid4())
                    if not ev.get("ts"):
                        ev["ts"] = L.utc_now()
                    ev["signature"] = ev.get("signature") or L.SIGNATURE_EVENT
                    ev["v"] = ev.get("v") or 1
                    ev["event_hash"] = L.compute_event_hash(ev)
                ok, _ = L.append_event(ev)
                if ok:
                    accepted += 1
            agg = L.rebuild_aggregate()
            return self._json(200, {"ok": True, "accepted": accepted, "total_plays": agg.get("total_plays")})

        return self._json(404, {"error": "not found"})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8777)
    ap.add_argument("--publish-every", type=int, default=0, help="HF publish after N new plays (0=off)")
    args = ap.parse_args()
    State.publish_every = args.publish_every
    L.ensure_dirs()
    if not L.AGGREGATE.exists():
        L.rebuild_aggregate()
    print(
        f"LYGO Play Ingest http://{args.host}:{args.port}/v1/  "
        f"publish_every={args.publish_every}",
        flush=True,
    )
    print("GET /v1/counts  POST /v1/play  (CORS *)", flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
