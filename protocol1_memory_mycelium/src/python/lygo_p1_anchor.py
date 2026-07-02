"""P1 Memory Mycelium with automatic LYGO anchoring."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional

from lygo_p1 import MemoryMycelium

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from lygo_anchor import MultiAnchor  # noqa: E402


class MemoryMyceliumAnchored:
    def __init__(self, anchor_mode: str | None = None, web3_key: Optional[str] = None):
        self.base = MemoryMycelium()
        import os

        if anchor_mode:
            os.environ.setdefault("LYGO_ANCHOR_MODE", anchor_mode)
        if web3_key:
            os.environ["WEB3_STORAGE_API_KEY"] = web3_key
        self.anchor = MultiAnchor()
        self.anchor_log: list[Any] = []

    def store(self, data: bytes, memory_id: Optional[str] = None) -> Dict:
        result = self.base.store(data, memory_id)
        mid = result["memory_id"]
        anchor_result = self.anchor.anchor_memory(mid, {"root_hash": result.get("root_hash"), "fragments": result.get("fragment_count")})
        self.anchor_log.append(anchor_result)
        result["anchor"] = {
            "id": anchor_result.id,
            "url": anchor_result.url,
            "service": anchor_result.service,
            "content_sha256": anchor_result.content_sha256,
        }
        return result

    def recall(self, memory_id: str) -> bytes:
        return self.base.recall(memory_id)