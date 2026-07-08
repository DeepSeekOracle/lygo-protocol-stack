#!/usr/bin/env python3
"""Verify local hardware attestation (Phase 6)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "stack"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="Emit JSON only")
    args = ap.parse_args()

    from protocol6_quantum_attest.measurement import MeasurementCollector, get_p0_hash, verify_p0_hash_against_golden
    from protocol6_quantum_attest.tpm_interface import check_tpm
    from protocol6_quantum_attest.puf_arbiter import check_puf
    from protocol6_quantum_attest.attestation import AttestationService

    health = MeasurementCollector().health()
    badge = AttestationService(MeasurementCollector(), node_id="LOCAL_VERIFY").generate_badge()
    self_ok = AttestationService(MeasurementCollector(), node_id="LOCAL_VERIFY").verify_badge(badge)

    report = {
        "signature": "Δ9Φ963-PHASE6-v1.0",
        "health": health,
        "p0_golden": get_p0_hash(),
        "p0_golden_ok": verify_p0_hash_against_golden(),
        "tpm_present": check_tpm(),
        "puf_present": check_puf(),
        "badge_signed": bool(badge.get("badge_signature")),
        "self_verify": self_ok,
        "status": "PASS" if self_ok and health.get("status") == "healthy" else "FAIL",
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())