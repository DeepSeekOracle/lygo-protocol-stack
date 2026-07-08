from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from protocol7_human_ai_interface.ble_gatt import parse_heart_rate_measurement


def test_parse_hr_with_rr():
    # flags: RR present (0x10), 8-bit HR
    data = bytes([0x10, 72, 0x00, 0x04])
    out = parse_heart_rate_measurement(data)
    assert out["heart_rate"] == 72
    assert len(out["ibi_ms"]) >= 1