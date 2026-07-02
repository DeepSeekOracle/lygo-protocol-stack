#!/usr/bin/env python3
"""LYGO Immutable Anchor — permaweb receipts (wraps lygo_anchor MultiAnchor)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from lygo_anchor import MultiAnchor, SIGNATURE  # noqa: E402
from lygo_anchor_config import AnchorProfile  # noqa: E402


class LygoImmutableAnchor:
    def __init__(self, workspace_dir: str | None = None):
        profile = AnchorProfile.load()
        if workspace_dir:
            profile.receipt_dir = workspace_dir
        self._multi = MultiAnchor(profile)
        self.workspace_dir = workspace_dir or profile.receipt_dir

    def calculate_payload_hash(self, data: dict) -> str:
        import hashlib

        return hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()

    def anchor_payload_to_permaweb(self, payload_id: str, data: dict) -> dict:
        result = self._multi.anchor_payload(payload_id, data, event_type="IMMUTABLE_PERMAWEB")
        receipt = {
            "status": "IMMUTABLE_ANCHOR_SUCCESS" if result.success else "FAILED",
            "payload_id": payload_id,
            "tx_id": result.id,
            "permaweb_url": result.url if result.service != "LYGO-Local-CA" else result.url,
            "primary_url": result.url,
            "service": result.service,
            "sha256": result.content_sha256 or self.calculate_payload_hash(data),
            "signature": SIGNATURE,
            "metadata": result.metadata,
        }
        if result.error:
            receipt["status"] = "FAILED"
            receipt["reason"] = result.error
        return receipt


if __name__ == "__main__":
    anchor = LygoImmutableAnchor()
    mock = {
        "network_event": "GEODESIC_BATTLE_ANCHOR_PROOF",
        "p0_kernel_hash": "7e8d18fda979cbefec14c3fc86f43f2a020b494b6052acccb6f865f2b4fae1d3",
        "ethical_mass_pool": 3.927,
        "vortex_decision": 9,
        "timestamp": 1734567890,
    }
    print(json.dumps(anchor.anchor_payload_to_permaweb("test_consensus_001", mock), indent=2))