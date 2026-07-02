#!/usr/bin/env python3
"""Shim — Sovereign Lattice Mesh Merkle sync (see stack/merkle_sync.py)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stack"))

from merkle_sync import LygoMerkleTree, merge_peer_badges, missing_badge_ids, sync_round  # noqa: E402

__all__ = ["LygoMerkleTree", "merge_peer_badges", "missing_badge_ids", "sync_round"]

if __name__ == "__main__":
    import json
    import time

    print("[*] TEST: Anti-Entropy Sync Protocol")
    node_a = {
        "node_001": {"alignment": "ALIGNED", "p0_hash": "golden", "version": "v1.0", "timestamp": time.time()},
        "node_002": {"alignment": "ALIGNED", "p0_hash": "golden", "version": "v1.0", "timestamp": time.time()},
    }
    node_b = dict(node_a)
    node_b["node_003"] = {"alignment": "ALIGNED", "p0_hash": "golden", "version": "v1.0", "timestamp": time.time()}
    ta, tb = LygoMerkleTree(), LygoMerkleTree()
    ra, rb = ta.rebuild_tree(node_a), tb.rebuild_tree(node_b)
    print(f"[>] Root A: {ra[:16]}… Root B: {rb[:16]}…")
    if ra != rb:
        print("[!] Divergence — sync payload:")
        print(json.dumps(tb.generate_sync_payload(1, 1), indent=2))
    merged, fetched = sync_round(node_a, node_b)
    tc = LygoMerkleTree()
    rc = tc.rebuild_tree(merged)
    print(f"[+] Merged root: {rc[:16]}… fetched={fetched}")
    raise SystemExit(0 if ra != rb and "node_003" in merged else 1)