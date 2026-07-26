#!/usr/bin/env python3
"""Minimal HTTP API for Dockerized LYGO community nodes."""

from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]


class _LightGossipBus:
    """Fallback when full lygo_stack is unavailable (sparse checkout / Layer D only)."""

    def __init__(self) -> None:
        self.local_node_id = os.environ.get("LYGO_NODE_ID", "DOCKER_NODE")
        self.gossip_recent: list[dict] = []
        self.peers: list[dict] = []
        self.peer_badges: dict[str, dict] = {}

    def publish_badge(self, from_node: str, badge: dict) -> dict:
        from datetime import datetime, timezone

        entry = {
            "node_id": from_node,
            "badge": badge,
            "ts": datetime.now(timezone.utc).isoformat(),
            "layer": badge.get("layer") or (badge.get("living_mesh") and "D") or "badge",
        }
        self.gossip_recent.append(entry)
        self.gossip_recent = self.gossip_recent[-200:]
        self.peer_badges[str(from_node)] = badge if isinstance(badge, dict) else {"raw": badge}
        return {"ok": True, "stored": True, "mode": "light_bus"}

    def snapshot(self) -> dict:
        return {
            "peers": self.peers,
            "gossip_recent": self.gossip_recent,
            "local_node_id": self.local_node_id,
            "badge_count": len(self.gossip_recent),
            "mode": "light_bus",
            "signature": "Δ9Φ963-PHASE5-MESH-GOSSIP-v1",
        }


_LIGHT_BUS = _LightGossipBus()
_STACK = None
_STACK_FAILED = False
_TLS = None


def _stack():
    import sys

    sys.path.insert(0, str(ROOT / "stack"))
    for sub in (
        "protocol0_byte_entropy_filter/src/python",
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


def get_tls_manager():
    global _TLS
    if _TLS is None:
        sys_path_tools = str(ROOT / "tools")
        if sys_path_tools not in __import__("sys").path:
            __import__("sys").path.insert(0, sys_path_tools)
        from tls_manager import TLSCertificateManager

        node = os.environ.get("LYGO_NODE_ID", "DOCKER_NODE")
        cert_dir = os.environ.get("LYGO_CERT_DIR", str(ROOT / "certs" / node))
        _TLS = TLSCertificateManager(node, cert_dir)
        if not _TLS.cert_file.is_file():
            _TLS.generate_self_signed()
    return _TLS


def get_stack():
    """Return full stack or None if unavailable (caller must handle)."""
    global _STACK, _STACK_FAILED
    if _STACK is not None:
        return _STACK
    if _STACK_FAILED:
        return None
    try:
        _STACK = _stack()
        return _STACK
    except Exception:
        _STACK_FAILED = True
        return None


def get_gossip_snapshot() -> dict:
    stack = get_stack()
    if stack is not None:
        try:
            return stack.federation.snapshot()
        except Exception:
            pass
    return _LIGHT_BUS.snapshot()


def ingest_gossip_badge(from_node: str, badge: dict) -> dict:
    stack = get_stack()
    if stack is not None:
        try:
            msg = stack.federation.gossip.publish_badge(str(from_node), badge)
            try:
                stack.slm.ingest_gossip_badge(str(from_node), badge)
                merkle = stack.slm.merkle.get_root_hash()
            except Exception:
                merkle = None
            return {
                "ok": True,
                "signature": "Δ9Φ963-SLM-v1.0",
                "gossip": msg,
                "merkle_root": merkle,
                "mode": "full_stack",
            }
        except Exception as e:
            # fall through to light bus
            pass
    msg = _LIGHT_BUS.publish_badge(str(from_node), badge)
    return {
        "ok": True,
        "signature": "Δ9Φ963-PHASE5-MESH-GOSSIP-v1",
        "gossip": msg,
        "merkle_root": None,
        "mode": "light_bus",
        "layer_d": True,
    }


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

    @staticmethod
    def _scalable_registry_root() -> str:
        reg_path = ROOT / "data" / "scalable_registry" / "registry.json"
        if not reg_path.is_file():
            return ""
        data = json.loads(reg_path.read_text(encoding="utf-8"))
        return str(data.get("global_merkle_root") or "")

    @staticmethod
    def _scalable_registry() -> dict:
        reg_path = ROOT / "data" / "scalable_registry" / "registry.json"
        if not reg_path.is_file():
            return {"signature": "Δ9Φ963-SCALABLE-REGISTRY-v1", "entries": [], "status": "empty"}
        data = json.loads(reg_path.read_text(encoding="utf-8"))
        return {
            "signature": "Δ9Φ963-SCALABLE-REGISTRY-v1",
            "global_merkle_root": data.get("global_merkle_root"),
            "entries": [
                {"id": e.get("id"), "merkle_root": e.get("merkle_root"), "metadata": e.get("metadata")}
                for e in data.get("entries", [])
            ],
        }

    @staticmethod
    def _kernel_eggs_registry() -> dict:
        reg_path = ROOT / "data" / "kernel_eggs" / "registry.json"
        if not reg_path.is_file():
            return {"signature": "Δ9Φ963-KERNEL-EGG-SOA-v1", "eggs": [], "status": "not_built"}
        data = json.loads(reg_path.read_text(encoding="utf-8"))
        return {
            "signature": "Δ9Φ963-KERNEL-EGG-SOA-v1",
            "registry_merkle_root": data.get("registry_merkle_root"),
            "git_head": data.get("git_head"),
            "retrieval_soa": data.get("retrieval_soa"),
            "anchor_registry": data.get("anchor_registry"),
            "eggs": [
                {
                    "egg_id": e.get("egg_id"),
                    "merkle_root": e.get("merkle_root"),
                    "content_sha256": (e.get("transport") or {}).get("content_sha256"),
                }
                for e in data.get("eggs", [])
            ],
            "anchored": data.get("anchored", []),
        }

    @staticmethod
    def _kernel_egg_detail(egg_id: str) -> dict | None:
        reg_path = ROOT / "data" / "kernel_eggs" / "registry.json"
        build_json = ROOT / "data" / "kernel_eggs" / "build" / f"{egg_id}.json"
        if build_json.is_file():
            return json.loads(build_json.read_text(encoding="utf-8"))
        if not reg_path.is_file():
            return None
        data = json.loads(reg_path.read_text(encoding="utf-8"))
        hit = next((e for e in data.get("eggs", []) if e.get("egg_id") == egg_id), None)
        if not hit:
            return None
        anchor = next((a for a in data.get("anchored", []) if a.get("egg_id") == egg_id), None)
        return {"egg_id": egg_id, "build": hit, "anchor": anchor, "retrieval_soa": data.get("retrieval_soa")}

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
        if path == "/registry":
            self._json(200, self._scalable_registry())
            return
        if path == "/registry/root":
            self._json(200, {"global_merkle_root": self._scalable_registry_root()})
            return
        if path == "/kernel/eggs":
            self._json(200, self._kernel_eggs_registry())
            return
        if path.startswith("/kernel/egg/"):
            egg_id = path.split("/kernel/egg/", 1)[-1].strip("/")
            body = self._kernel_egg_detail(egg_id)
            if body is None:
                self._json(404, {"error": "unknown egg", "egg_id": egg_id})
                return
            self._json(200, body)
            return
        if path == "/badge" or path == "/badge/living":
            import sys

            tools = ROOT / "tools"
            if str(tools) not in sys.path:
                sys.path.insert(0, str(tools))
            # Prefer Layer D living mesh badge (includes A/B/C roots)
            try:
                from collect_living_mesh_badge import collect_living_badge  # noqa: E402

                badge = collect_living_badge(quick=True)
            except Exception:
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
            snap = get_gossip_snapshot()
            recent = snap.get("gossip_recent") or []
            self._json(
                200,
                {
                    "peers": snap.get("peers", []),
                    "badge_count": len(recent),
                    "gossip_recent": recent,
                    "local_node_id": snap.get("local_node_id"),
                    "mode": snap.get("mode"),
                    "signature": "Δ9Φ963-PHASE5-MESH-GOSSIP-v1",
                },
            )
            return
        if path.startswith("/badge/"):
            node_id = path.split("/")[-1]
            stack = get_stack()
            if stack is not None:
                try:
                    slm = stack.slm
                    if node_id in slm.peer_badges:
                        self._json(200, {"node_id": node_id, "badge": slm.peer_badges[node_id]})
                        return
                except Exception:
                    pass
            if node_id in _LIGHT_BUS.peer_badges:
                self._json(200, {"node_id": node_id, "badge": _LIGHT_BUS.peer_badges[node_id]})
                return
            snap = get_gossip_snapshot()
            for entry in reversed(snap.get("gossip_recent") or []):
                if str(entry.get("node_id")) == node_id:
                    self._json(200, entry.get("badge") or entry)
                    return
            self._json(404, {"error": "node badge not in gossip log", "node_id": node_id})
            return
        if path == "/gossip/root":
            stack = get_stack()
            if stack is not None:
                try:
                    slm = stack.slm
                    slm.rebuild_from_gossip_log(get_gossip_snapshot().get("gossip_recent") or [])
                    self._json(200, slm.gossip_root())
                    return
                except Exception:
                    pass
            self._json(
                200,
                {
                    "mode": "light_bus",
                    "badge_count": len(_LIGHT_BUS.gossip_recent),
                    "nodes": list(_LIGHT_BUS.peer_badges.keys()),
                    "signature": "Δ9Φ963-PHASE5-MESH-GOSSIP-v1",
                },
            )
            return
        if path == "/slm/snapshot":
            stack = get_stack()
            if stack is not None:
                try:
                    self._json(200, stack.slm.snapshot())
                    return
                except Exception as e:
                    self._json(503, {"error": str(e), "mode": "stack_error"})
                    return
            self._json(
                200,
                {
                    "mode": "light_bus",
                    "note": "full SLM unavailable (sparse checkout) — Layer D gossip bus active",
                    "peer_badges": list(_LIGHT_BUS.peer_badges.keys()),
                    "badge_count": len(_LIGHT_BUS.gossip_recent),
                },
            )
            return
        if path == "/cert/pin":
            self._json(200, get_tls_manager().pin_payload())
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
                    "/badge/living",
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
                    "GET /cert/pin",
                    "POST /cert/pin",
                    "POST /gossip/pin",
                    "POST /synthesis/run",
                    "/kernel/eggs",
                    "/kernel/egg/{egg_id}",
                ],
            },
        )

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/gossip/badge":
            body = self._read_json_body()
            badge = body.get("badge") or body
            from_node = body.get("from") or body.get("node_id") or (
                badge.get("node_id") if isinstance(badge, dict) else None
            ) or "remote"
            badge_obj = badge if isinstance(badge, dict) else {"raw": badge}
            result = ingest_gossip_badge(str(from_node), badge_obj)
            self._json(200, result)
            return
        if path == "/gossip/sync":
            body = self._read_json_body()
            stack = get_stack()
            if stack is not None:
                try:
                    slm = stack.slm
                    if isinstance(body.get("peer_badges"), dict):
                        slm.merge_remote_badges(body["peer_badges"])
                    self._json(200, slm.gossip_sync(body))
                    return
                except Exception as e:
                    self._json(503, {"error": str(e)})
                    return
            # light bus merge
            if isinstance(body.get("peer_badges"), dict):
                for nid, b in body["peer_badges"].items():
                    _LIGHT_BUS.publish_badge(str(nid), b if isinstance(b, dict) else {"raw": b})
            self._json(200, {"ok": True, "mode": "light_bus", "snapshot": _LIGHT_BUS.snapshot()})
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
            if out.get("ok"):
                try:
                    stack = get_stack()
                    stack._anchor_stack_event("CONSENSUS", {"proposal_id": body.get("proposal_id"), "vote": out})
                except Exception:
                    pass
            code = 200 if out.get("ok") else 400
            self._json(code, out)
            return
        if path == "/anchor/event":
            body = self._read_json_body()
            event_type = str(body.get("event_type") or "GENERIC")
            payload = body.get("payload") if isinstance(body.get("payload"), dict) else body
            stack = get_stack()
            stack._anchor_stack_event(event_type, payload)
            if str(ROOT / "stack") not in sys.path:
                sys.path.insert(0, str(ROOT / "stack"))
            from lygo_stack_anchor import get_orchestrator

            drained = get_orchestrator().drain_queue(max_jobs=4)
            self._json(200, {"ok": True, "signature": "Δ9Φ963-ANCHOR-v1", "processed": drained})
            return
        if path == "/anchor/drain":
            if str(ROOT / "stack") not in sys.path:
                sys.path.insert(0, str(ROOT / "stack"))
            from lygo_stack_anchor import get_orchestrator

            drained = get_orchestrator().drain_queue()
            self._json(200, {"ok": True, "drained": drained})
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
        if path in ("/cert/pin", "/gossip/pin"):
            body = self._read_json_body()
            node_id = str(body.get("node_id") or body.get("from") or "")
            pin = str(body.get("pin") or "")
            expiry = body.get("expiry")
            if not node_id or not pin:
                self._json(400, {"error": "node_id and pin required"})
                return
            mgr = get_tls_manager()
            mgr.ingest_peer_pin(node_id, pin, str(expiry) if expiry else None)
            self._json(200, {"ok": True, "node_id": node_id, "signature": "Δ9Φ963-PHASE9-TLS-v1.0"})
            return
        if path == "/synthesis/run":
            body = self._read_json_body()
            seed = body.get("seed") or body.get("seed_hex")
            if not seed:
                live = self._p7_live_seed()
                seed = live.get("seed") or live.get("seed_hex")
            out_rel = str(body.get("output") or "tools/lygo_control_center/workspace/synthesis_output.wav")
            duration = float(body.get("duration_sec") or body.get("duration") or 5.0)
            import sys as _sys

            if str(ROOT / "tools") not in _sys.path:
                _sys.path.insert(0, str(ROOT / "tools"))
            from live_synthesis import generate_audio_from_seed

            result = generate_audio_from_seed(str(seed), ROOT / out_rel, duration_sec=duration)
            self._json(200, result)
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
    ap.add_argument("--tls", action="store_true", help="Serve HTTPS with node certificate")
    ap.add_argument("--cert-dir", default=None, help="Certificate directory (sets LYGO_CERT_DIR)")
    args = ap.parse_args()
    if args.cert_dir:
        os.environ["LYGO_CERT_DIR"] = args.cert_dir
    srv = HTTPServer((args.host, args.port), Handler)
    scheme = "http"
    if args.tls:
        import ssl

        mgr = get_tls_manager()
        ctx = mgr.ssl_server_context()
        srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
        scheme = "https"
    print(f"LYGO node API on {scheme}://{args.host}:{args.port}")
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())