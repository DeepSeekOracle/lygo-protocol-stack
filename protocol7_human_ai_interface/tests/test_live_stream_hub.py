"""Live stream hub + synthetic PDU parse."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from protocol7_human_ai_interface import live_stream_hub as hub
from protocol7_human_ai_interface.ble_gatt import parse_heart_rate_measurement


def test_hub_ibi_and_seed():
    hub.reset("test")
    hub.record_ibi(820, 1, h_min=0.5)
    hub.record_ibi(810, 2, h_min=0.55)
    snap = hub.snapshot()
    assert snap["latest_ibi_ms"] == 810
    assert len(snap["ibi_history"]) == 2
    hub.record_seed("a" * 64, h_min=0.9, ibi_count=64)
    snap2 = hub.snapshot()
    assert snap2["seed_256"] == "a" * 64
    assert snap2["buffer_size"] == 0


def test_fake_hr_pdu_rr():
    ibi_ms = 850
    rr = int((ibi_ms / 1000.0) * 1024)
    pdu = bytes([0x10, 75, rr & 0xFF, (rr >> 8) & 0xFF])
    out = parse_heart_rate_measurement(pdu)
    assert out["ibi_ms"]
    assert abs(out["ibi_ms"][0] - ibi_ms) <= 2