#!/usr/bin/env python3
"""Generate synthetic IBI / biometric samples for Phase 7 entropy tests."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from protocol7_human_ai_interface.entropy_extraction import extract_p0_seed_from_ibi


def synthetic_ibi(n: int = 24, base_hr: float = 72.0, noise: float = 40.0) -> list[float]:
    rng = random.Random(963528174)
    ibi = []
    for _ in range(n):
        ibi.append(60000.0 / base_hr + rng.uniform(-noise, noise))
    return ibi


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=24)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    ibi = synthetic_ibi(args.samples)
    pack = extract_p0_seed_from_ibi(ibi)
    out = {"ibi_ms": ibi, "extraction": pack, "signature": "Δ9Φ963-PHASE7-v1.0"}
    print(json.dumps(out, indent=2))
    return 0 if pack.get("seed_256") else 1


if __name__ == "__main__":
    raise SystemExit(main())