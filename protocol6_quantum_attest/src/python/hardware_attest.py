"""P6 hardware attestation seal (platform fingerprint, no secrets)."""

from __future__ import annotations

import hashlib
import platform
import uuid
from typing import Any


def collect_hardware_signals() -> dict[str, str]:
    return {
        "platform": platform.platform(),
        "processor": platform.processor() or "unknown",
        "machine": platform.machine(),
        "node": platform.node(),
        "mac_int": str(uuid.getnode()),
    }


def attestation_seal(extra: str = "") -> dict[str, Any]:
    signals = collect_hardware_signals()
    canonical = "|".join(f"{k}={signals[k]}" for k in sorted(signals)) + f"|extra={extra}"
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {
        "signature": "Δ9Φ963-P6-ATTEST-SEAL-v1",
        "seal": digest[:32],
        "signals": signals,
        "p0_sub_key_hint": digest[:16],
    }


def validate_against(stored_seal: str, extra: str = "") -> bool:
    current = attestation_seal(extra=extra)["seal"]
    return current == stored_seal