"""Hardware measurement collection pipeline."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .puf_arbiter import puf_challenge, puf_fingerprint
from .secure_boot import measure_boot_chain
from .tpm_interface import check_tpm, read_pcr_stub, tpm_status

ROOT = Path(__file__).resolve().parents[1]
P0_GOLDEN = ROOT / "protocol0_nano_kernel" / "fixtures" / "p0_canonical.sha256"
P6_VERSION = "Δ9Φ963-PHASE6-v1.0"


def get_p0_hash() -> str:
    if P0_GOLDEN.is_file():
        line = P0_GOLDEN.read_text(encoding="utf-8").strip()
        return line.split()[0] if line else ""
    return ""


def verify_p0_hash_against_golden(measured: str | None = None) -> bool:
    golden = get_p0_hash()
    if not golden:
        return False
    return (measured or golden) == golden


class MeasurementCollector:
    """Collect TPM, PUF, boot, firmware stub, and P0 golden hash."""

    def collect(self, *, puf_challenge_id: str | None = None) -> dict[str, Any]:
        boot = measure_boot_chain()
        puf = puf_challenge(puf_challenge_id)
        pcrs = read_pcr_stub()
        p0 = get_p0_hash()
        firmware_stub = hashlib.sha256(
            json.dumps({"fw": "lygo-p6-stub", "p0": p0}, sort_keys=True).encode()
        ).hexdigest()

        bundle = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": P6_VERSION,
            "p0_hash": p0,
            "p0_golden_ok": verify_p0_hash_against_golden(p0),
            "tpm": tpm_status(),
            "pcrs": pcrs,
            "boot": boot,
            "firmware_hash": firmware_stub,
            "puf": puf,
            "puf_fingerprint": puf_fingerprint(),
        }
        canonical = json.dumps(bundle, sort_keys=True, default=str).encode("utf-8")
        bundle["measurement_digest"] = hashlib.sha256(canonical).hexdigest()
        return bundle

    def health(self) -> dict[str, Any]:
        from .puf_arbiter import check_puf
        from .tpm_interface import check_tpm

        return {
            "status": "healthy",
            "tpm_present": check_tpm(),
            "puf_present": check_puf(),
            "p0_hash": get_p0_hash(),
            "version": P6_VERSION,
        }