"""P1 workflow memory — fragmented store under stack data/sandcastle/mycelium."""

from __future__ import annotations

import json
import hashlib
import time
from pathlib import Path
from typing import Any, Optional

SIGNATURE = "Δ9Φ963-SANDCASTLE-SOVEREIGN-v1.0"


def default_mycelium_root() -> Path:
    root = Path(__file__).resolve().parents[1]
    return root / "data" / "sandcastle" / "mycelium"


class P1MemoryMycelium:
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or default_mycelium_root()
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.fragment_count = 12
        self.threshold = 10

    def store(self, data: dict[str, Any]) -> str:
        memory_id = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()[:16]
        json_data = json.dumps(data, indent=2)
        fragment_size = max(1, len(json_data) // self.fragment_count)
        fragments: list[str] = []
        for i in range(self.fragment_count):
            start = i * fragment_size
            end = (i + 1) * fragment_size if i < self.fragment_count - 1 else len(json_data)
            chunk = json_data[start:end]
            fragment_path = self.storage_path / f"{memory_id}_{i:02d}.frag"
            fragment_path.write_text(chunk, encoding="utf-8")
            fragments.append(str(fragment_path))
        manifest = {
            "memory_id": memory_id,
            "fragments": fragments,
            "threshold": self.threshold,
            "timestamp": time.time(),
            "signature": SIGNATURE,
        }
        (self.storage_path / f"{memory_id}_manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        ledger = self.storage_path.parent / "manifest.jsonl"
        ledger.parent.mkdir(parents=True, exist_ok=True)
        with ledger.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "memory_id": memory_id},
                    sort_keys=True,
                )
                + "\n"
            )
        return memory_id

    def recall(self, memory_id: str) -> Optional[dict[str, Any]]:
        manifest_path = self.storage_path / f"{memory_id}_manifest.json"
        if not manifest_path.is_file():
            return None
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        json_data = ""
        for frag_path in manifest.get("fragments", []):
            p = Path(frag_path)
            if p.is_file():
                json_data += p.read_text(encoding="utf-8")
        if len(json_data) < 2:
            return None
        try:
            return json.loads(json_data)
        except json.JSONDecodeError:
            return None