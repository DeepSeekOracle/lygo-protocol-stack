"""LYGO Anchor subsystem tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "stack"))
sys.path.insert(0, str(ROOT / "protocol1_memory_mycelium" / "src" / "python"))


def test_multi_anchor_local_roundtrip():
    from lygo_anchor import MultiAnchor
    from lygo_anchor_config import AnchorProfile

    profile = AnchorProfile.from_env()
    profile.mode = "local"
    m = MultiAnchor(profile, ROOT)
    r = m.anchor_payload("test_unit", {"hello": "lygo"}, "TEST")
    assert r.success
    assert r.content_sha256
    assert (ROOT / "data" / "anchors" / f"{r.content_sha256}.json").is_file()


def test_orchestrator_queue_drain():
    from lygo_stack_anchor import AnchorOrchestrator

    orch = AnchorOrchestrator(ROOT)
    path = orch.enqueue("TEST", {"x": 1}, "test_queue_drain")
    assert path.is_file()
    done = orch.drain_queue()
    assert any(d.get("payload_id") == "test_queue_drain" for d in done)


def test_p1_anchored_store():
    from lygo_p1_anchor import MemoryMyceliumAnchored

    m = MemoryMyceliumAnchored(anchor_mode="local")
    out = m.store(b"anchor-test-payload", "unit-mem")
    assert out.get("anchor", {}).get("content_sha256")