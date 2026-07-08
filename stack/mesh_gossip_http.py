"""Phase 5 — HTTPS badge gossip between LYGO community nodes (epidemic summaries)."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

SIGNATURE = "Δ9Φ963-PHASE5-MESH-GOSSIP-v1"
DEFAULT_TIMEOUT = 12


@dataclass
class GossipPeer:
    node_id: str
    base_url: str  # e.g. http://127.0.0.1:8787
    tls_pin_sha256: str | None = None  # human-gated for production wide-area


def _request_json(url: str, *, method: str = "GET", body: dict | None = None, timeout: int = DEFAULT_TIMEOUT) -> dict:
    data = None
    headers = {"User-Agent": "LYGO-Mesh-Gossip/1.0", "Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_remote_badge(peer: GossipPeer) -> dict:
    url = peer.base_url.rstrip("/") + "/badge"
    try:
        badge = _request_json(url)
        return {"ok": True, "peer": peer.node_id, "badge": badge}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"ok": False, "peer": peer.node_id, "error": str(exc)[:200]}


def post_badge_to_peer(peer: GossipPeer, badge: dict) -> dict:
    url = peer.base_url.rstrip("/") + "/gossip/badge"
    try:
        ack = _request_json(url, method="POST", body={"from": badge.get("node_id", "unknown"), "badge": badge})
        return {"ok": True, "peer": peer.node_id, "ack": ack}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"ok": False, "peer": peer.node_id, "error": str(exc)[:200]}


def epidemic_round(local_badge: dict, peers: list[GossipPeer], federation: Any) -> dict:
    """Pull badges from peers, merge into federation gossip bus."""
    pulls = [fetch_remote_badge(p) for p in peers]
    merged = []
    for item in pulls:
        if item.get("ok") and federation is not None:
            b = item.get("badge") or {}
            node = item.get("peer", "peer")
            msg = federation.gossip.publish_badge(node, b if isinstance(b, dict) else {"raw": b})
            merged.append(msg)
    return {
        "signature": SIGNATURE,
        "pulls": pulls,
        "merged_count": len(merged),
        "local_status": local_badge.get("status"),
    }