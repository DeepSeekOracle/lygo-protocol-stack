"""Phase 3–4 — Community mesh: node registry, worker pool, alignment gossip."""

from __future__ import annotations

import json
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class PeerNode:
    node_id: str
    endpoint: str
    alignment_badge: str = "UNVERIFIED"
    last_seen: float = field(default_factory=time.time)
    phase: int = 2


class NodeRegistry:
    """Phase 3 — register community LYGO nodes (local-first; no network required)."""

    def __init__(self) -> None:
        self._peers: dict[str, PeerNode] = {}
        self._lock = threading.Lock()

    def register(self, node_id: str, endpoint: str, *, badge: str = "UNVERIFIED", phase: int = 2) -> PeerNode:
        peer = PeerNode(node_id=node_id, endpoint=endpoint, alignment_badge=badge, phase=phase)
        with self._lock:
            self._peers[node_id] = peer
        return peer

    def heartbeat(self, node_id: str, *, badge: str | None = None) -> bool:
        with self._lock:
            p = self._peers.get(node_id)
            if not p:
                return False
            p.last_seen = time.time()
            if badge:
                p.alignment_badge = badge
            return True

    def list_peers(self) -> list[dict]:
        with self._lock:
            return [
                {
                    "node_id": p.node_id,
                    "endpoint": p.endpoint,
                    "alignment_badge": p.alignment_badge,
                    "phase": p.phase,
                    "last_seen": p.last_seen,
                }
                for p in self._peers.values()
            ]


class MeshGossip:
    """Phase 4 — propagate alignment badge summaries (in-process bus; extend to HTTP later)."""

    def __init__(self, registry: NodeRegistry) -> None:
        self.registry = registry
        self._log: list[dict] = []
        self._lock = threading.Lock()

    def publish_badge(self, node_id: str, badge_payload: dict) -> dict:
        msg = {
            "id": uuid.uuid4().hex[:16],
            "node_id": node_id,
            "ts": time.time(),
            "badge": badge_payload,
        }
        with self._lock:
            self._log.append(msg)
            if len(self._log) > 500:
                self._log = self._log[-250:]
        status = str(badge_payload.get("status", "UNKNOWN"))
        self.registry.heartbeat(node_id, badge=status)
        return msg

    def recent(self, limit: int = 20) -> list[dict]:
        with self._lock:
            return list(self._log[-limit:])


class HorizontalWorkerPool:
    """Phase 4 — parallel falsifiable-vector / audit workloads."""

    def __init__(self, workers: int = 4) -> None:
        self.workers = max(1, workers)
        self._executor = ThreadPoolExecutor(max_workers=self.workers, thread_name_prefix="lygo-worker")

    def map_vectors(
        self,
        items: list[tuple[dict, str]],
        fn: Callable[[dict, str], dict],
    ) -> list[dict]:
        futures = [self._executor.submit(fn, vec, cat) for vec, cat in items]
        out: list[dict] = []
        for fut in as_completed(futures):
            try:
                out.append(fut.result())
            except Exception as exc:
                out.append({"error": str(exc), "passed": False})
        return out

    def shutdown(self, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait)


class FederationRuntime:
    version = "Δ9Φ963-PHASE3-4-FEDERATION-v1"

    def __init__(self, local_node_id: str = "lygo-local", workers: int = 4) -> None:
        self.local_node_id = local_node_id
        self.registry = NodeRegistry()
        self.gossip = MeshGossip(self.registry)
        self.pool = HorizontalWorkerPool(workers=workers)
        self.registry.register(local_node_id, "local://stack", phase=4)

    def announce_alignment(self, badge: dict) -> dict:
        return self.gossip.publish_badge(self.local_node_id, badge)

    def snapshot(self) -> dict:
        return {
            "version": self.version,
            "local_node_id": self.local_node_id,
            "peers": self.registry.list_peers(),
            "gossip_recent": self.gossip.recent(5),
            "workers": self.pool.workers,
        }


if __name__ == "__main__":
    rt = FederationRuntime()
    rt.announce_alignment({"status": "ALIGNED", "signature": "Δ9Φ963-PHASE2-DEPLOYMENT"})
    print(json.dumps(rt.snapshot(), indent=2))