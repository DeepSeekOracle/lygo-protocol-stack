from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from protocol7_human_ai_interface.ethical_mapping import EthicalVectorMapper


def test_ethical_mapping():
    mapper = EthicalVectorMapper()
    state = {
        "aggregated": {
            "heart_rate": 85,
            "hrv": 30,
            "stress_level": 0.8,
            "activity_steps": 5000,
            "battery": 0.5,
        }
    }
    vector = mapper.map_to_ethical_vector(state)
    assert len(vector) == 3
    assert all(0 <= x <= 1 for x in vector)

    state["aggregated"] = {
        "heart_rate": 65,
        "hrv": 80,
        "stress_level": 0.2,
        "activity_steps": 12000,
        "battery": 0.9,
    }
    vector2 = mapper.map_to_ethical_vector(state)
    assert vector2[0] > 0.5
    assert vector2[1] > 0.5
    assert vector2[2] > 0.5