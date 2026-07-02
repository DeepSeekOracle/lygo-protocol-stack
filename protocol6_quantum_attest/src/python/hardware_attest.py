"""P6 hardware attestation seal (platform fingerprint, no secrets)."""

from __future__ import annotations

import hashlib
import platform
import sys
import uuid
from pathlib import Path
from typing import Any

_PKG = Path(__file__).resolve().parents[2]
if str(_PKG.parent) not in sys.path:
    sys.path.insert(0, str(_PKG.parent))


def collect_hardware_signals() -> dict[str, str]:
    return {
        "platform": platform.platform(),
        "processor": platform.processor() or "unknown",
        "machine": platform.machine(),
        "node": platform.node(),
        "mac_int": str(uuid.getnode()),
    }


def attestation_seal(extra: str = "") -> dict[str, Any]:
    try:
        from protocol6_quantum_attest.attestation import AttestationService
        from protocol6_quantum_attest.measurement import MeasurementCollector

        badge = AttestationService(MeasurementCollector(), node_id="SEAL_PROBE").generate_badge()
        signals = collect_hardware_signals()
        return {
            "signature": "Δ9Φ963-P6-ATTEST-SEAL-v2",
            "seal": str(badge.get("measurement_digest", ""))[:32],
            "signals": signals,
            "p0_sub_key_hint": str(badge.get("p0_hash", ""))[:16],
            "badge_signature": badge.get("badge_signature"),
            "extra": extra,
        }
    except Exception:
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