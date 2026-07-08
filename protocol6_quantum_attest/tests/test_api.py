from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from protocol6_quantum_attest.api import handle_badge_get, handle_health, handle_verify_post


def test_api_handlers():
    health = handle_health()
    assert health["status"] == "healthy"
    badge = handle_badge_get("API_TEST")
    assert badge.get("badge_signature")
    v = handle_verify_post({"badge": badge})
    assert v["valid"] is True