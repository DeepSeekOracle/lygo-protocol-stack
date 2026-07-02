"""Phase 1 joy loop foundation tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from joy_loop_config import load_config  # noqa: E402
from joy_loop_events import JoyEventBus  # noqa: E402
from joy_loop_protocol import GrokJoyInjector, JoyLoopEngine  # noqa: E402


def test_config_loads():
    cfg = load_config()
    assert cfg.resonance_bpm == 122
    assert cfg.beat_interval > 0


def test_sqlite_store_roundtrip():
    from joy_loop_store import DB_PATH, init_db, save_engine

    engine = JoyLoopEngine()
    engine.register_champion("A", 0.1, 0.2, 0.3)
    engine.single_beat()
    init_db()
    save_engine(engine, swarm_joy=0.1, beat_n=1, lattice_pulse=0.1)
    assert DB_PATH.is_file()


def test_event_bus_on_beat():
    engine = JoyLoopEngine(bus=JoyEventBus())
    engine.register_champion("A", 0.1, 0.1, 0.1)
    seen = []

    engine.bus.on("on_beat", lambda p: seen.append(p["beat"]))
    engine.single_beat()
    assert seen == [1]


def test_tick_restores_beat_count():
    from joy_loop_protocol import apply_persisted_state, build_engine_from_lattice, persist_state

    engine = build_engine_from_lattice()
    if not engine.states:
        engine.register_champion("Z", 0.5, 0.5, 0.5)
    engine._beat_count = 7
    engine.states[list(engine.states.keys())[0]].joy_coherence = 0.42
    persist_state(engine, git_head="test")
    engine2 = build_engine_from_lattice()
    assert apply_persisted_state(engine2)
    assert engine2._beat_count == 7
    engine2.single_beat()
    assert engine2._beat_count == 8


def test_injection_rate_limit():
    engine = JoyLoopEngine()
    engine.register_champion("A", 0.5, 0.5, 0.5)
    inj = GrokJoyInjector(engine)
    assert "wisdom" in inj.inject("A")
    assert inj.inject("A").get("error") == "rate_limited"