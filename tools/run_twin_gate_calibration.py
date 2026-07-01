#!/usr/bin/env python3
"""Live twin-gate calibration: 6 edge dilemmas — text (severity) + byte receipts."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stack"))

from lygo_stack import deploy_stack  # noqa: E402

SCENARIOS = ROOT / "tests" / "pilot_edge_scenarios.json"
OUT = ROOT / "tests" / "twin_gate_calibration_last_run.json"


def main() -> int:
    data = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    stack = deploy_stack("TWIN_GATE_CALIBRATION")
    rows = []
    print("TWIN GATE CALIBRATION — live text + byte per scenario")
    for sc in data.get("scenarios", []):
        q = sc["query"]
        sev = float(sc.get("severity", 0.8))
        cat = sc.get("byte_category", "high_entropy_dilemma")
        ent = float(sc.get("entropy_level", 0.85))
        text = stack.process_ethical_query(q, severity=sev, purpose=f"twin_{sc['id']}")
        vector = {
            "id": sc["id"],
            "payload": {
                "claim": q,
                "entropy_level": ent,
                "layer1_sovereignty": "enforced",
                "primordial_law": True,
            },
        }
        byte = stack.process_falsifiable_vector(vector, category=cat)
        t0 = text.get("p0") or {}
        row = {
            "id": sc["id"],
            "label": sc.get("label"),
            "severity": sev,
            "text": {
                "verdict": t0.get("verdict"),
                "phi_risk": t0.get("phi_risk", t0.get("risk")),
                "hash": t0.get("hash"),
                "light_code": text.get("light_code"),
            },
            "byte": {
                "category": cat,
                "entropy_level": ent,
                "verdict": byte.get("decision"),
                "phi_risk": byte.get("phi_risk"),
                "hash": byte.get("p0_hash"),
                "gate_len": byte.get("gate_len"),
                "repair": byte.get("repair_triggered"),
                "light_code": byte.get("light_code"),
            },
            "delta_phi": round(float(byte.get("phi_risk", 0)) - float(t0.get("phi_risk", t0.get("risk", 0))), 4),
        }
        rows.append(row)
        print(
            f"{sc['id']}: text {row['text']['verdict']} phi={row['text']['phi_risk']} | "
            f"byte {row['byte']['verdict']} phi={row['byte']['phi_risk']} | Δ={row['delta_phi']}"
        )

    payload = {
        "signature": "Δ9Φ963-TWIN-GATE-CALIBRATION-v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scenarios": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())