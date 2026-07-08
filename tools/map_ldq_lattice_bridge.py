#!/usr/bin/env python3
"""Report LDQ module map: HF Space vs stack P8 (lattice intel helper)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HF = ROOT.parent / "Hugging face"
P8 = ROOT / "protocol8_ldq_synthesis"
OUT = ROOT / "tests" / "ldq_lattice_bridge_last_run.json"


def main() -> int:
    hf_ldq = sorted(HF.glob("ldq_*.py")) if HF.is_dir() else []
    p8 = sorted(P8.glob("*.py")) if P8.is_dir() else []
    vault = ROOT.parent / "LYGO Data Quantization (LDQ) Protoc.txt"
    report = {
        "signature": "Δ9Φ963-LDQ-BRIDGE-MAP-v1",
        "hf_ldq_modules": [p.name for p in hf_ldq],
        "stack_p8_modules": [p.name for p in p8 if p.name != "__init__.py"],
        "ldq_vault_present": vault.is_file(),
        "ldq_vault_bytes": vault.stat().st_size if vault.is_file() else 0,
        "intel_index": "docs/LYGO_LATTICE_INTEL_INDEX.json",
        "recommendation": "Restore HF factory (HF_SPACE_REBUILD_POINTER Phase 1) before copying ldq_* into protocol8.",
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())