from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from protocol6_quantum_attest.measurement import MeasurementCollector, get_p0_hash, verify_p0_hash_against_golden


def test_p0_golden():
    h = get_p0_hash()
    assert len(h) == 64
    assert verify_p0_hash_against_golden(h)


def test_collect_digest():
    c = MeasurementCollector()
    m1 = c.collect()
    m2 = c.collect()
    assert m1["measurement_digest"]
    assert m1["p0_golden_ok"] is True
    assert m1["puf_fingerprint"] == m2["puf_fingerprint"]


def test_health():
    h = MeasurementCollector().health()
    assert h["status"] == "healthy"
    assert h["version"] == "Δ9Φ963-PHASE6-v1.0"