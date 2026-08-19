#!/usr/bin/env python3
"""Hardware / geodesic attestation stub for deadman eternal base (basic real receipt).

If lygo geodesic sealer tools exist, record a local receipt. Otherwise write a
honest stub receipt — never fake hardware roots.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "deadman" / "hardware_attestation_receipt.json"


def main() -> int:
    geo = ROOT / "clawhub" / "mirrors" / "lygo-geodesic-sealer"
    now = datetime.now(timezone.utc).isoformat()
    receipt = {
        "signature": "Delta9Phi963-DEADMAN-HW-ATTEST-STUB-v1",
        "created_utc": now,
        "target": "NODE_LIGHTFATHER_ETERNAL_BASE",
        "status": "stub_local",
        "geodesic_skill_present": geo.is_dir(),
        "note": (
            "Basic runnable placeholder. Pair later with real HAIP / geodesic attest. "
            "Does not invent TPM quotes."
        ),
        "binds": {
            "origin": "docs/seals/LIGHTFATHER_IRREPLACEABLE_ORIGIN.json",
            "manifest": "data/deadman/DEADMAN_MANIFEST_v2.json",
        },
    }
    if (ROOT / "docs" / "seals" / "LIGHTFATHER_IRREPLACEABLE_ORIGIN.json").is_file():
        import hashlib
        receipt["origin_sha256"] = hashlib.sha256(
            (ROOT / "docs" / "seals" / "LIGHTFATHER_IRREPLACEABLE_ORIGIN.json").read_bytes()
        ).hexdigest()
    OUT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
