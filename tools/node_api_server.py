#!/usr/bin/env python3
"""Minimal HTTP API for Dockerized LYGO community nodes."""

from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

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
    @staticmethod
    def _p6_health() -> dict:
        import sys

        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from protocol6_quantum_attest.measurement import MeasurementCollector

        return MeasurementCollector().health()

    @staticmethod
    def _p7_biometric_state() -> dict:
        import sys

        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from protocol7_human_ai_interface.api import handle_biometric_state

        return handle_biometric_state()

    @staticmethod
    def _p7_live_seed() -> dict:
        import json as _json

        seed_path = ROOT / "tools" / "lygo_control_center" / "workspace" / "latest_seed.json"
        if not seed_path.is_file():
            return {"status": "no_live_seed", "signature": "Δ9Φ963-PHASE7-POLISH-v1.0"}
        try:
            return {**_json.loads(seed_path.read_text(encoding="utf-8")), "status": "ok"}
        except _json.JSONDecodeError:
            return {"status": "corrupt", "signature": "Δ9Φ963-PHASE7-POLISH-v1.0"}

    @staticmethod
    def _p7_history(seconds: int) -> list:
        import sys

        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from protocol7_human_ai_interface.api import handle_biometric_history

        return handle_biometric_history(seconds)

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
        if path == "/attestation/health":
            self._json(200, self._p6_health())
            return
        if path == "/attestation/badge":
            self._json(200, get_stack().get_hardware_badge())
            return
        if path == "/biometric/state":
            self._json(200, self._p7_biometric_state())
            return
        if path == "/biometric/live_seed":
            self._json(200, self._p7_live_seed())
            return
        if path == "/biometric/history":
            qs = parse_qs(urlparse(self.path).query)
            seconds = int((qs.get("seconds") or ["60"])[0])
            self._json(200, {"samples": self._p7_history(seconds), "signature": "Δ9Φ963-PHASE7-v1.0"})
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
            slm = get_stack().slm
            if node_id in slm.peer_badges:
                self._json(200, {"node_id": node_id, "badge": slm.peer_badges[node_id]})
                return
            snap = get_stack().federation.snapshot()
            for entry in reversed(snap.get("gossip_recent") or []):
                if str(entry.get("node_id")) == node_id:
                    self._json(200, entry.get("badge") or entry)
                    return
            self._json(404, {"error": "node badge not in gossip log", "node_id": node_id})
            return
        if path == "/gossip/root":
            slm = get_stack().slm
            slm.rebuild_from_gossip_log(get_stack().federation.snapshot().get("gossip_recent") or [])
            self._json(200, slm.gossip_root())
            return
        if path == "/slm/snapshot":
            self._json(200, get_stack().slm.snapshot())
            return
        if path.startswith("/mycelium/fragment/"):
            frag_id = path.rsplit("/", 1)[-1]
            frag = get_stack().slm.mycelium.get_fragment(frag_id)
            if frag:
                self._json(200, frag)
            else:
                self._json(404, {"error": "fragment not found", "fragment_id": frag_id})
            return
        if path.startswith("/mycelium/reconstruct/"):
            data_id = path.rsplit("/", 1)[-1]
            self._json(200, get_stack().slm.mycelium.reconstruct(data_id))
            return
        if path.startswith("/consensus/result/"):
            pid = path.rsplit("/", 1)[-1]
            res = get_stack().slm.proposals.get_result(pid)
            if res:
                self._json(200, res)
            else:
                self._json(404, {"error": "unknown proposal", "proposal_id": pid})
            return
        self._json(
            404,
            {
                "error": "not found",
                "paths": [
                    "/health",
                    "/badge",
                    "/badge/{node_id}",
                    "/attestation/health",
                    "/attestation/badge",
                    "POST /attestation/verify",
                    "/biometric/state",
                    "/biometric/history",
                    "POST /device/register",
                    "/demo",
                    "/elasticity",
                    "/federation",
                    "/gossip",
                    "POST /gossip/badge",
                    "POST /gossip/scatter",
                    "GET /gossip/root",
                    "POST /gossip/sync",
                    "POST /mycelium/store",
                    "GET /mycelium/fragment/{id}",
                    "GET /mycelium/reconstruct/{data_id}",
                    "POST /consensus/propose",
                    "POST /consensus/vote",
                    "GET /consensus/result/{id}",
                    "GET /slm/snapshot",
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
            badge_obj = badge if isinstance(badge, dict) else {"raw": badge}
            msg = stack.federation.gossip.publish_badge(str(from_node), badge_obj)
            stack.slm.ingest_gossip_badge(str(from_node), badge_obj)
            self._json(200, {"ok": True, "signature": "Δ9Φ963-SLM-v1.0", "gossip": msg, "merkle_root": stack.slm.merkle.get_root_hash()})
            return
        if path == "/gossip/sync":
            body = self._read_json_body()
            slm = get_stack().slm
            if isinstance(body.get("peer_badges"), dict):
                slm.merge_remote_badges(body["peer_badges"])
            self._json(200, slm.gossip_sync(body))
            return
        if path == "/mycelium/store":
            body = self._read_json_body()
            data_id = str(body.get("data_id") or "memory_auto")
            raw = body.get("data") or body.get("payload") or ""
            out = get_stack().slm.mycelium.store(data_id, raw)
            self._json(200, out)
            return
        if path == "/consensus/propose":
            body = self._read_json_body()
            prop = get_stack().slm.proposals.propose(
                str(body.get("author") or get_stack()._sovereign_id),
                str(body.get("title") or "proposal"),
                str(body.get("description") or ""),
            )
            self._json(200, prop)
            return
        if path == "/consensus/vote":
            body = self._read_json_body()
            mass = float(body.get("ethical_mass") or 1.0)
            out = get_stack().slm.proposals.vote(
                str(body.get("proposal_id")),
                str(body.get("node_id") or os.environ.get("LYGO_NODE_ID", "NODE")),
                int(body.get("vote", 9)),
                mass,
            )
            code = 200 if out.get("ok") else 400
            self._json(code, out)
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
        if path == "/attestation/verify":
            body = self._read_json_body()
            badge = body.get("badge") if isinstance(body.get("badge"), dict) else body
            stack = get_stack()
            badge_obj = badge if isinstance(badge, dict) else {}
            detailed = stack.attestation.verify_badge_detailed(badge_obj)
            self._json(
                200,
                {
                    "valid": detailed.get("valid", False),
                    "alignment": detailed.get("alignment"),
                    "ethical_gate": detailed.get("ethical_gate"),
                    "reasons": detailed.get("reasons", []),
                    "signature": "Δ9Φ963-P6-POLISH-v1.0",
                },
            )
            return
        if path == "/device/register":
            body = self._read_json_body()
            import sys

            if str(ROOT) not in sys.path:
                sys.path.insert(0, str(ROOT))
            from protocol7_human_ai_interface.api import handle_register

            out = handle_register(body)
            code = 400 if out.get("status") == "error" else 200
            self._json(code, {**out, "signature": "Δ9Φ963-PHASE7-v1.0"})
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