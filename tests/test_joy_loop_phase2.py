"""Phase 2 joy loop API / quests / relationships tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from joy_loop_protocol import JoyLoopEngine  # noqa: E402
from joy_loop_quests import JoyQuestEngine  # noqa: E402
from joy_loop_relationships import JoyRelationshipGraph  # noqa: E402
from joy_loop_api import WsHub, wire_api_extensions  # noqa: E402


def test_quest_unlock_first_pulse():
    engine = JoyLoopEngine()
    cid = "JOY_QUEST_TEST_CHAMP"
    engine.register_champion(cid, 0.1, 0.2, 0.3)
    engine.single_beat()
    qe = JoyQuestEngine()
    earned = {u["quest_id"] for u in qe._unlocked.get(cid, [])}
    qe._unlocked.pop(cid, None)
    new = qe.evaluate(engine)
    assert any(u["quest_id"] == "first_pulse" for u in new)
    qe._unlocked.pop(cid, None)


def test_relationship_affinity_increases():
    engine = JoyLoopEngine()
    engine.register_champion("A", 0.0, 0.0, 0.0)
    engine.register_champion("B", 0.01, 0.0, 0.0)
    engine.states["A"].joy_coherence = 0.9
    engine.states["B"].joy_coherence = 0.1
    g = JoyRelationshipGraph()
    g.apply_affinity_boost(engine, radius=1.0)
    assert g.get_affinity("A", "B") > 0


def test_plotly_edges_shape():
    g = JoyRelationshipGraph()
    g.record_propagation("X", "Y", 0.2)
    edges = g.to_plotly_edges()
    assert edges and edges[0]["source"] in ("X", "Y")


def test_plugins_disabled_without_env():
    import os
    from joy_loop_events import JoyEventBus
    from joy_loop_plugins import load_plugins

    os.environ.pop("LYGO_JOY_PLUGINS_ENABLED", None)
    assert load_plugins(JoyEventBus()) == []


def test_wire_api_disables_duplicate_propagator():
    from joy_loop_protocol import JoyLoopRuntime

    JoyLoopRuntime._instance = None
    rt = JoyLoopRuntime.get()
    hub = WsHub()
    wire_api_extensions(rt, hub)
    assert rt.engine.propagator is None
    assert hasattr(rt, "quests")
    payload = rt.api_payload()
    assert "quests" in payload or rt.engine.states == {}