from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from protocol6_quantum_attest.attestation import AttestationService
from protocol6_quantum_attest.measurement import MeasurementCollector


def test_badge_sign_and_verify():
    att = AttestationService(MeasurementCollector(), node_id="TEST_NODE")
    badge = att.generate_badge()
    assert badge.get("signed") is True
    assert att.verify_badge(badge)


def test_tamper_fails():
    att = AttestationService(MeasurementCollector(), node_id="TEST_NODE")
    badge = att.generate_badge()
    badge["node_id"] = "EVIL"
    assert not att.verify_badge(badge)


def test_verify_detailed_aligned():
    att = AttestationService(MeasurementCollector(), node_id="TEST_NODE")
    badge = att.generate_badge()
    d = att.verify_badge_detailed(badge)
    assert d["alignment"] == "ALIGNED"
    assert d["ethical_gate"] is True
    assert d["valid"] is True