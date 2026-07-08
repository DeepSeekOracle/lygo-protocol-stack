from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from protocol7_human_ai_interface.device_abstraction import create_adapter, GarminAdapter, OuraAdapter


def test_create_adapters():
    g = create_adapter("garmin", "g1", "simulated")
    assert isinstance(g, GarminAdapter)
    g.connect()
    assert g.read().heart_rate is not None
    o = create_adapter("oura", "o1", "simulated")
    assert isinstance(o, OuraAdapter)