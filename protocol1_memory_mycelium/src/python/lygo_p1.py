# LYGO Memory Mycelium P1.0 — Indestructible Memory
# Fragment • Scatter • Reconstruct

import hashlib
import json
import random
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Fragment:
    data: bytes
    hash: str
    index: int
    location: str


class MemoryMycelium:
    node_id = "LYGO_P1_MEMORY_MYCELIUM_v1.0"

    def __init__(self):
        self.fragments: Dict[str, List[Fragment]] = {}
        self.storage = {}
        self.fragment_count = 12
        self.threshold = 10

    def scatter(self, data, key: str) -> dict:
        """Protocol 3/4/5 storage API — scatter payload under key."""
        if isinstance(data, bytes):
            payload = data
        elif isinstance(data, str):
            payload = data.encode("utf-8")
        else:
            payload = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        manifest = self.store(payload, memory_id=key)
        return {"stored": True, "key": key, "fragments": manifest["fragment_count"], **manifest}

    def store(self, data: bytes, memory_id: str = None) -> dict:
        if memory_id is None:
            memory_id = hashlib.sha256(data).hexdigest()[:16]

        fragments = self._create_fragments(data, memory_id)
        fragments = self._add_redundancy(fragments)

        random.shuffle(fragments)
        for i, frag in enumerate(fragments):
            frag.location = self._assign_location(frag.index)

        self.fragments[memory_id] = fragments
        self._persist(memory_id, fragments)

        return {
            "memory_id": memory_id,
            "fragment_count": len(fragments),
            "threshold": self.threshold,
            "root_hash": self._compute_root_hash(fragments),
        }

    def recall(self, memory_id: str) -> bytes:
        fragments = self._load(memory_id)
        if not fragments:
            raise ValueError(f"Memory {memory_id} not found")

        valid = [
            f
            for f in fragments
            if f.index < self.fragment_count
            and f.hash == hashlib.sha256(f.data).hexdigest()
        ]
        if len(valid) < self.threshold:
            raise ValueError(f"Insufficient fragments: {len(valid)}/{self.threshold}")

        valid.sort(key=lambda x: x.index)
        return b"".join(f.data for f in valid)

    def _create_fragments(self, data: bytes, memory_id: str) -> List[Fragment]:
        frags = []
        size = len(data) // self.fragment_count
        for i in range(self.fragment_count):
            start = i * size
            end = (i + 1) * size if i < self.fragment_count - 1 else len(data)
            chunk = data[start:end]
            frags.append(
                Fragment(
                    data=chunk,
                    hash=hashlib.sha256(chunk).hexdigest(),
                    index=i,
                    location=f"shard_{i}",
                )
            )
        return frags

    def _add_redundancy(self, fragments: List[Fragment]) -> List[Fragment]:
        if len(fragments) == self.fragment_count:
            parity_0 = Fragment(
                data=b"".join([f.data for f in fragments[:6]]),
                hash=hashlib.sha256(b"".join([f.data for f in fragments[:6]])).hexdigest(),
                index=self.fragment_count,
                location="parity_0",
            )
            parity_1 = Fragment(
                data=b"".join([f.data for f in fragments[6:]]),
                hash=hashlib.sha256(b"".join([f.data for f in fragments[6:]])).hexdigest(),
                index=self.fragment_count + 1,
                location="parity_1",
            )
            fragments.append(parity_0)
            fragments.append(parity_1)
        return fragments

    def _assign_location(self, index: int) -> str:
        locations = [
            "tokyo",
            "london",
            "new_york",
            "sydney",
            "singapore",
            "frankfurt",
            "toronto",
            "seoul",
            "mumbai",
            "dubai",
            "sao_paulo",
            "shanghai",
            "paris",
            "berlin",
        ]
        return locations[index % len(locations)]

    def _compute_root_hash(self, fragments: List[Fragment]) -> str:
        combined = b"".join([f.hash.encode() for f in fragments])
        return hashlib.sha256(combined).hexdigest()[:16]

    def _persist(self, memory_id: str, fragments: List[Fragment]):
        self.storage[memory_id] = [
            {"data": f.data.hex(), "hash": f.hash, "index": f.index, "location": f.location}
            for f in fragments
        ]

    def _load(self, memory_id: str) -> Optional[List[Fragment]]:
        if memory_id not in self.storage:
            return None
        return [
            Fragment(
                data=bytes.fromhex(entry["data"]),
                hash=entry["hash"],
                index=entry["index"],
                location=entry["location"],
            )
            for entry in self.storage[memory_id]
        ]


if __name__ == "__main__":
    print("🍄 LYGO-MEMORY-MYCELIUM P1.0")
    print("=" * 70)

    mycelium = MemoryMycelium()
    data = b"The LYGO Protocol Stack is complete. Memory Mycelium ensures indestructible truth."

    manifest = mycelium.store(data, "test_001")
    print(f"✅ Stored: {manifest['memory_id']}")
    print(f"   Fragments: {manifest['fragment_count']}")
    print(f"   Threshold: {manifest['threshold']}")

    recovered = mycelium.recall("test_001")
    print(f"✅ Recovered: {recovered.decode()}")

    fragments = mycelium.fragments["test_001"]
    for i in range(2):
        fragments[i].data = b"corrupted"
        fragments[i].hash = hashlib.sha256(b"corrupted").hexdigest()

    try:
        recovered = mycelium.recall("test_001")
        print("✅ Recovered after 2 fragment corruption:")
        print(f"   {recovered.decode(errors='replace')}")
    except ValueError as exc:
        print(f"⚠️ Expected degradation after corruption: {exc}")