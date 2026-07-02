#!/usr/bin/env python3
"""
P7 Quantum Drive entropy harness (stub).
Injects high-entropy noise into a phi_risk perturbation slot for observer-opaque decisions
while P0 kernel replay remains deterministic given the same entropy draw record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "stack"))


def draw_entropy(nbytes: int = 32) -> bytes:
    return secrets.token_bytes(nbytes) + os.urandom(nbytes)


def phi_perturbation(base_phi: float, entropy: bytes, scale: float = 0.001) -> float:
    h = int(hashlib.sha256(entropy).hexdigest()[:8], 16)
    unit = (h % 10000) / 10000.0
    return max(0.0, min(1.0, base_phi + (unit - 0.5) * scale))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-phi", type=float, default=0.4045)
    ap.add_argument("--ibi-from", choices=("os", "simulate"), default="os")
    args = ap.parse_args()

    if args.ibi_from == "simulate":
        from protocol7_human_ai_interface.entropy_extraction import BiometricEntropyHarness

        harness = BiometricEntropyHarness()
        pack = harness.from_biometric_state(
            {"ibi_ms": [800.0 + i * 2.5 for i in range(24)], "aggregated": {"heart_rate": 72}}
        )
        seed_hex = pack["seed_256"]
        phi_p = harness.phi_perturbation(args.base_phi, seed_hex)
        out = {
            "signature": "Δ9Φ963-PHASE7-v1.0",
            "mode": "ibi_simulate",
            "entropy_pack": pack,
            "base_phi": args.base_phi,
            "phi_perturbed": phi_p,
        }
    else:
        ent = draw_entropy()
        out = {
            "signature": "Δ9Φ963-PHASE7-v1.0",
            "mode": "os_random",
            "entropy_hex": ent.hex()[:64],
            "base_phi": args.base_phi,
            "phi_perturbed": phi_perturbation(args.base_phi, ent),
        }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())