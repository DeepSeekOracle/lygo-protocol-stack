"""FPGA PUF arbiter — software challenge-response until hardware is wired."""

from __future__ import annotations

import hashlib
import hmac
import platform
import uuid
from typing import Any


def _device_salt() -> bytes:
    parts = (
        platform.machine(),
        platform.node(),
        str(uuid.getnode()),
        platform.processor() or "cpu",
    )
    return hashlib.sha256("|".join(parts).encode("utf-8")).digest()


def check_puf() -> bool:
    """True when PUF path is available (software arbiter always on; FPGA pending)."""
    return True


def puf_challenge(challenge: str | None = None) -> dict[str, Any]:
    """Delay-PUF style response (deterministic per device, unique across devices)."""
    ch = challenge or "LYGO-P6-DEFAULT-CHALLENGE"
    key = _device_salt()
    response = hmac.new(key, ch.encode("utf-8"), hashlib.sha256).hexdigest()
    return {
        "challenge": ch,
        "response": response,
        "arbiter": "software",
        "fpga_pending": True,
    }


def puf_fingerprint() -> str:
    return puf_challenge("LYGO-P6-FINGERPRINT")["response"][:32]