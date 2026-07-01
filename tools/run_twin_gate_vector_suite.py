#!/usr/bin/env python3
"""40+ vector twin-gate convergence: semantic text path vs byte path per claim."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / "tests" / "test_falsifiable_vectors.json"
OUT = ROOT / "tests" / "twin_gate_vector_suite_last_run.json"

sys.path.insert(0, str(ROOT / "stack"))
from lygo_stack import deploy_stack  # noqa: E402

SIGNATURE = "Δ9Φ963-TWIN-GATE-VECTOR-SUITE-v1"


def main() -> int:
    data = json.loads(VECTORS.read_text(encoding="utf-8"))
    stack = deploy_stack("TWIN_GATE_VECTOR_SUITE")
    rows = []
    verdict_match = 0
    deltas = []

    print("=" * 72)
    print(" TWIN GATE — 40+ VECTOR CONVERGENCE SUITE")
    print(f" {SIGNATURE}")
    print("=" * 72)

    for category, vectors in (data.get("categories") or {}).items():
        for vec in vectors:
            claim = (vec.get("payload") or {}).get("claim", "")
            ent = float((vec.get("payload") or {}).get("entropy_level", 0.5))
            sw = ent
            text = stack.process_ethical_query(
                claim,
                severity=sw,
                severity_weight=sw,
                audit_category=category,
                purpose=f"vec_{vec.get('id')}",
            )
            byte = stack.process_falsifiable_vector(vec, category=category)
            t0 = text.get("p0") or {}
            tv = str(t0.get("verdict", ""))
            bv = str(byte.get("decision", ""))
            tp = float(t0.get("phi_risk", t0.get("risk", 0)))
            bp = float(byte.get("phi_risk", 0))
            dphi = round(bp - tp, 4)
            deltas.append(abs(dphi))
            if tv == bv:
                verdict_match += 1
            rows.append(
                {
                    "id": vec.get("id"),
                    "category": category,
                    "text_verdict": tv,
                    "byte_verdict": bv,
                    "text_phi": round(tp, 4),
                    "byte_phi": round(bp, 4),
                    "delta_phi": dphi,
                    "verdict_match": tv == bv,
                    "expected": vec.get("expected_decision"),
                }
            )

    total = len(rows)
    payload = {
        "signature": SIGNATURE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "verdict_match_count": verdict_match,
        "verdict_match_rate": round(100.0 * verdict_match / max(1, total), 2),
        "mean_abs_delta_phi": round(sum(deltas) / max(1, len(deltas)), 4),
        "max_abs_delta_phi": round(max(deltas) if deltas else 0, 4),
        "rows": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Vectors: {total}")
    print(f"Verdict match (text vs byte): {verdict_match}/{total} ({payload['verdict_match_rate']}%)")
    print(f"Mean |Δφ|: {payload['mean_abs_delta_phi']} | max |Δφ|: {payload['max_abs_delta_phi']}")
    print(f"Report: {OUT}")
    return 0 if verdict_match >= total else 1


if __name__ == "__main__":
    raise SystemExit(main())