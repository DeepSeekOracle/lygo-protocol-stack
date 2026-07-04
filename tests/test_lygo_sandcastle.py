from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def example_yaml() -> str:
    p = ROOT / "lygo_sandcastle" / "workflows" / "example_sovereign.yaml"
    return p.read_text(encoding="utf-8")


def test_p0_gatekeeper(example_yaml: str) -> None:
    from lygo_sandcastle.gatekeeper import P0Gatekeeper

    g = P0Gatekeeper()
    out = g.validate(example_yaml)
    assert out["verdict"] in ("AMPLIFY", "SOFTEN", "QUARANTINE")


def test_p5_harmony() -> None:
    from lygo_sandcastle.harmony import P5HarmonyNode

    ident = P5HarmonyNode().create_node({"name": "t", "agent": "local"})
    assert ident["light_code"].startswith("LF-Δ9-")
    assert "ethical_mass" in ident


def test_p1_memory_roundtrip(tmp_path: Path) -> None:
    from lygo_sandcastle.memory import P1MemoryMycelium

    mem = P1MemoryMycelium(tmp_path)
    mid = mem.store({"test": "data"})
    assert mem.recall(mid) == {"test": "data"}


def test_run_pipeline(example_yaml: str, tmp_path: Path) -> None:
    from lygo_sandcastle.orchestrator import LYGOWorkflowOrchestrator

    orch = LYGOWorkflowOrchestrator(mycelium=tmp_path)
    out = orch.run(example_yaml, skip_anchor=False)
    assert out.get("ok") is True
    assert out.get("memory_id")