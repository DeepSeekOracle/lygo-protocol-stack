from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from protocol7_human_ai_interface.device_abstraction import AppleWatchAdapter, BiometricReading


def test_apple_watch_simulation():
    adapter = AppleWatchAdapter("test_watch", "simulated")
    assert adapter.connect() is True
    reading = adapter.read()
    assert isinstance(reading, BiometricReading)
    assert reading.heart_rate is not None
    assert 50 <= reading.heart_rate <= 100
    assert reading.hrv is not None
    assert 40 <= reading.hrv <= 80