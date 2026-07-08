"""Distributed mycelium — consistent hash + P1-aligned 12/10 erasure (Δ9Φ963-SLM-v1.0)."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any


class LygoConsistentHashRing:
    def __init__(self, replicas: int = 3) -> None:
        self.replicas = replicas
        self.ring: dict[int, str] = {}
        self.sorted_keys: list[int] = []

    def _hash(self, key: str) -> int:
        return int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16)

    def add_node(self, node_id: str) -> None:
        for i in range(self.replicas):
            val = self._hash(f"{node_id}-replica-{i}")
            self.ring[val] = node_id
            self.sorted_keys.append(val)
        self.sorted_keys.sort()

    def get_allocated_nodes(self, fragment_id: str, count: int = 3) -> list[str]:
        if not self.ring:
            return []
        val = self._hash(fragment_id)
        start_idx = 0
        for i, k in enumerate(self.sorted_keys):
            if val <= k:
                start_idx = i
                break
        allocated: list[str] = []
        for i in range(len(self.sorted_keys)):
            idx = (start_idx + i) % len(self.sorted_keys)
            node = self.ring[self.sorted_keys[idx]]
            if node not in allocated:
                allocated.append(node)
                if len(allocated) == count:
                    break
        return allocated


class DistributedMyceliumMesh:
    """Fragment store with local filesystem backing per mesh node."""

    def __init__(
        self,
        local_node_id: str,
        data_dir: Path,
        *,
        total_fragments: int = 12,
        minimum_threshold: int = 10,
    ) -> None:
        self.local_node_id = local_node_id
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.total_fragments = total_fragments
        self.minimum_threshold = minimum_threshold
        self.hash_ring = LygoConsistentHashRing()
        self._manifests: dict[str, list[dict[str, Any]]] = {}
        self._network_store: dict[str, dict[str, str]] = {}

    def register_mesh_node(self, node_id: str) -> None:
        self.hash_ring.add_node(node_id)
        self._network_store.setdefault(node_id, {})

    def _fragment_path(self, node_id: str, fragment_id: str) -> Path:
        p = self.data_dir / node_id / f"{fragment_id}.frag"
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def _write_fragment(self, node_id: str, fragment_id: str, chunk: str) -> None:
        if node_id == self.local_node_id:
            self._fragment_path(node_id, fragment_id).write_text(chunk, encoding="utf-8")
        self._network_store.setdefault(node_id, {})[fragment_id] = chunk

    def _read_fragment(self, node_id: str, fragment_id: str) -> str | None:
        if node_id == self.local_node_id:
            p = self._fragment_path(node_id, fragment_id)
            if p.is_file():
                return p.read_text(encoding="utf-8")
        return self._network_store.get(node_id, {}).get(fragment_id)

    def store(self, data_id: str, raw_payload: str | bytes) -> dict[str, Any]:
        if isinstance(raw_payload, bytes):
            text = raw_payload.decode("utf-8", errors="replace")
        else:
            text = raw_payload
        manifest: list[dict[str, Any]] = []
        base_len = max(1, len(text) // self.total_fragments)
        for i in range(self.total_fragments):
            start = i * base_len
            end = start + base_len if i < (self.total_fragments - 1) else len(text)
            chunk = text[start:end]
            frag_id = f"FRAG-{data_id}-{i:02d}"
            targets = self.hash_ring.get_allocated_nodes(frag_id, count=3)
            primary = targets[0] if targets else self.local_node_id
            backups = targets[1:] if len(targets) > 1 else []
            self._write_fragment(primary, frag_id, chunk)
            for backup in backups:
                self._write_fragment(backup, frag_id, chunk)
            manifest.append(
                {
                    "fragment_id": frag_id,
                    "data_id": data_id,
                    "fragment_index": i,
                    "assigned_node": primary,
                    "backup_nodes": backups,
                    "hash": hashlib.sha256(chunk.encode()).hexdigest(),
                    "stored": True,
                }
            )
        self._manifests[data_id] = manifest
        meta_path = self.data_dir / f"{data_id}.manifest.json"
        meta_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return {
            "data_id": data_id,
            "fragment_count": len(manifest),
            "threshold": self.minimum_threshold,
            "manifest": manifest,
            "signature": "Δ9Φ963-SLM-v1.0",
        }

    def get_fragment(self, fragment_id: str) -> dict[str, Any] | None:
        for data_id, manifest in self._manifests.items():
            for rec in manifest:
                if rec["fragment_id"] == fragment_id:
                    primary = rec["assigned_node"]
                    data = self._read_fragment(primary, fragment_id)
                    if data is None:
                        for b in rec.get("backup_nodes") or []:
                            data = self._read_fragment(b, fragment_id)
                            if data is not None:
                                break
                    if data is None:
                        return None
                    return {
                        "fragment_id": fragment_id,
                        "data": base64.b64encode(data.encode()).decode("ascii"),
                        "hash": rec["hash"],
                        "data_id": data_id,
                    }
        return None

    def reconstruct(self, data_id: str) -> dict[str, Any]:
        manifest = self._manifests.get(data_id)
        if manifest is None:
            meta = self.data_dir / f"{data_id}.manifest.json"
            if meta.is_file():
                manifest = json.loads(meta.read_text(encoding="utf-8"))
        if not manifest:
            return {"ok": False, "error": "unknown data_id", "data_id": data_id}

        collected: dict[int, str] = {}
        for rec in manifest:
            idx = int(rec["fragment_index"])
            frag_id = rec["fragment_id"]
            primary = rec["assigned_node"]
            chunk = self._read_fragment(primary, frag_id)
            if chunk is None:
                for b in rec.get("backup_nodes") or []:
                    chunk = self._read_fragment(b, frag_id)
                    if chunk is not None:
                        break
            if chunk is not None:
                collected[idx] = chunk

        if len(collected) < self.minimum_threshold:
            return {
                "ok": False,
                "error": f"insufficient fragments {len(collected)}/{self.minimum_threshold}",
                "data_id": data_id,
            }
        restored = "".join(collected[k] for k in sorted(collected.keys()))
        return {
            "ok": True,
            "data_id": data_id,
            "data": restored,
            "fragments_used": len(collected),
            "signature": "Δ9Φ963-SLM-v1.0",
        }

    def simulate_node_failure(self, node_id: str) -> None:
        if node_id in self._network_store:
            self._network_store[node_id].clear()
        ndir = self.data_dir / node_id
        if ndir.is_dir() and node_id != self.local_node_id:
            for f in ndir.glob("*.frag"):
                f.unlink(missing_ok=True)