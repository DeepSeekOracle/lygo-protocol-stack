"""Anti-entropy sync — Merkle tree over peer badges (Δ9Φ963-SLM-v1.0)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass
class MerkleNode:
    hash_val: str
    left: MerkleNode | None = None
    right: MerkleNode | None = None
    badge_data: dict[str, Any] | None = None
    node_id: str | None = None

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None


class LygoMerkleTree:
    def __init__(self) -> None:
        self.root: MerkleNode | None = None
        self.leaves: list[MerkleNode] = []
        self.node_map: dict[str, MerkleNode] = {}

    @staticmethod
    def calculate_hash(data: str) -> str:
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    @classmethod
    def compute_leaf_hash(cls, node_id: str, badge: dict[str, Any]) -> str:
        serialized = json.dumps(badge, sort_keys=True, default=str)
        return cls.calculate_hash(f"{node_id}||{serialized}")

    def rebuild_tree(self, peer_badges: dict[str, dict[str, Any]]) -> str:
        if not peer_badges:
            self.root = None
            self.leaves = []
            self.node_map = {}
            return ""

        self.leaves = []
        self.node_map = {}
        for n_id in sorted(peer_badges.keys()):
            badge = peer_badges[n_id]
            leaf_hash = self.compute_leaf_hash(n_id, badge)
            node = MerkleNode(hash_val=leaf_hash, badge_data=badge, node_id=n_id)
            self.leaves.append(node)
            self.node_map[n_id] = node

        current_level = self.leaves[:]
        while len(current_level) > 1:
            next_level: list[MerkleNode] = []
            for i in range(0, len(current_level), 2):
                left_child = current_level[i]
                if i + 1 < len(current_level):
                    right_child = current_level[i + 1]
                else:
                    right_child = MerkleNode(
                        hash_val=left_child.hash_val,
                        left=left_child.left,
                        right=left_child.right,
                    )
                combined = self.calculate_hash(left_child.hash_val + right_child.hash_val)
                next_level.append(MerkleNode(hash_val=combined, left=left_child, right=right_child))
            current_level = next_level

        self.root = current_level[0]
        return self.root.hash_val

    def get_root_hash(self) -> str:
        return self.root.hash_val if self.root else ""

    def get_node_by_level_index(self, target_level: int, target_index: int) -> MerkleNode | None:
        if not self.root:
            return None
        current_level_nodes = [self.root]
        current_depth = 0
        while current_depth < target_level:
            next_level_nodes: list[MerkleNode] = []
            for node in current_level_nodes:
                if node.is_leaf:
                    next_level_nodes.append(node)
                else:
                    if node.left:
                        next_level_nodes.append(node.left)
                    if node.right:
                        next_level_nodes.append(node.right)
            if not next_level_nodes:
                break
            current_level_nodes = next_level_nodes
            current_depth += 1
        if target_index < len(current_level_nodes):
            return current_level_nodes[target_index]
        return None

    def generate_sync_payload(self, level: int, index: int) -> dict[str, Any]:
        node = self.get_node_by_level_index(level, index)
        if not node:
            return {"root_hash": self.get_root_hash(), "level": level, "index": index, "hash": None}
        return {
            "root_hash": self.get_root_hash(),
            "level": level,
            "index": index,
            "hash": node.hash_val,
            "left_child": node.left.hash_val if node.left else None,
            "right_child": node.right.hash_val if node.right else None,
            "badge_data": node.badge_data if node.is_leaf else None,
            "node_id": node.node_id if node.is_leaf else None,
            "signature": "Δ9Φ963-SLM-v1.0",
        }


def missing_badge_ids(local: dict[str, dict], remote: dict[str, dict]) -> list[str]:
    return sorted(set(remote.keys()) - set(local.keys()))


def merge_peer_badges(local: dict[str, dict], remote: dict[str, dict]) -> dict[str, dict]:
    out = dict(local)
    out.update(remote)
    return out


def sync_round(local_badges: dict[str, dict], remote_badges: dict[str, dict]) -> tuple[dict[str, dict], list[str]]:
    """One push-pull round: return merged catalog and ids fetched this round."""
    missing = missing_badge_ids(local_badges, remote_badges)
    merged = merge_peer_badges(local_badges, {k: remote_badges[k] for k in missing})
    return merged, missing