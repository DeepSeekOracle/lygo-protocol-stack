"""Sovereign Lattice Mesh runtime — Merkle gossip + mycelium + consensus."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from distributed_mycelium_mesh import DistributedMyceliumMesh
from harmonic_consensus_mesh import HarmonicConsensusEngine, ProposalManager
from merkle_sync import LygoMerkleTree, merge_peer_badges, missing_badge_ids, sync_round

SLM_VERSION = "Δ9Φ963-SLM-v1.0"


class SovereignLatticeMesh:
    def __init__(self, local_node_id: str, repo_root: Path) -> None:
        self.local_node_id = local_node_id
        self.peer_badges: dict[str, dict[str, Any]] = {}
        self.merkle = LygoMerkleTree()
        data_dir = repo_root / "data" / "slm_mycelium"
        self.mycelium = DistributedMyceliumMesh(local_node_id, data_dir)
        self.mycelium.register_mesh_node(local_node_id)
        self.consensus_engine = HarmonicConsensusEngine()
        self.proposals = ProposalManager(self.consensus_engine)
        self._sync_stats: dict[str, Any] = {"rounds": 0, "last_convergence_ms": 0}

    def register_mesh_node(self, node_id: str) -> None:
        self.mycelium.register_mesh_node(node_id)

    def ingest_gossip_badge(self, node_id: str, badge: dict[str, Any]) -> None:
        self.peer_badges[node_id] = badge
        self.merkle.rebuild_tree(self.peer_badges)

    def rebuild_from_gossip_log(self, gossip_recent: list[dict]) -> str:
        for entry in gossip_recent:
            nid = str(entry.get("node_id", ""))
            badge = entry.get("badge") if isinstance(entry.get("badge"), dict) else entry
            if nid:
                self.peer_badges[nid] = badge
        return self.merkle.rebuild_tree(self.peer_badges)

    def gossip_root(self) -> dict[str, Any]:
        return {
            "root_hash": self.merkle.get_root_hash(),
            "badge_count": len(self.peer_badges),
            "local_node_id": self.local_node_id,
            "signature": SLM_VERSION,
        }

    def gossip_sync(self, body: dict[str, Any]) -> dict[str, Any]:
        level = int(body.get("level", 0))
        index = int(body.get("index", 0))
        remote_root = body.get("root_hash")
        payload = self.merkle.generate_sync_payload(level, index)
        if remote_root and remote_root != self.merkle.get_root_hash():
            payload["divergent"] = True
            payload["missing_local"] = missing_badge_ids(self.peer_badges, body.get("peer_badges") or {})
        return payload

    def merge_remote_badges(self, remote: dict[str, dict]) -> dict[str, Any]:
        t0 = time.perf_counter()
        merged, fetched = sync_round(self.peer_badges, remote)
        self.peer_badges = merged
        self.merkle.rebuild_tree(self.peer_badges)
        self._sync_stats["rounds"] = int(self._sync_stats.get("rounds", 0)) + 1
        self._sync_stats["last_convergence_ms"] = int((time.perf_counter() - t0) * 1000)
        return {
            "merged": len(merged),
            "fetched": fetched,
            "root_hash": self.merkle.get_root_hash(),
            "rounds": self._sync_stats["rounds"],
            "signature": SLM_VERSION,
        }

    def converge(self, remote_catalogs: list[dict[str, dict]], max_rounds: int = 3) -> dict[str, Any]:
        """Merge up to max_rounds peer catalogs (in-process mesh sim)."""
        for _ in range(max_rounds):
            changed = False
            for remote in remote_catalogs:
                before = len(self.peer_badges)
                self.merge_remote_badges(remote)
                if len(self.peer_badges) > before:
                    changed = True
            if not changed:
                break
        roots = {self.merkle.get_root_hash()}
        for remote in remote_catalogs:
            t = LygoMerkleTree()
            t.rebuild_tree(merge_peer_badges(self.peer_badges, remote))
            roots.add(t.get_root_hash())
        return {
            "converged": len(roots) == 1,
            "unique_roots": len(roots),
            "badge_count": len(self.peer_badges),
            "rounds": self._sync_stats["rounds"],
            "signature": SLM_VERSION,
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "version": SLM_VERSION,
            "local_node_id": self.local_node_id,
            "merkle_root": self.merkle.get_root_hash(),
            "badge_count": len(self.peer_badges),
            "mesh_nodes": list(self.mycelium.hash_ring.ring.values()),
            "sync": self._sync_stats,
        }