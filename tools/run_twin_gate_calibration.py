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
        sw = float(sc.get("severity_weight", sev))
        text = stack.process_ethical_query(
            q, severity=sev, severity_weight=sw, purpose=f"twin_{sc['id']}"
        )
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
            "severity_weight": sw,
            "text": {
                "verdict": t0.get("verdict"),
                "phi_risk": t0.get("phi_risk", t0.get("risk")),
                "p0_raw_phi": t0.get("p0_raw_phi"),
                "p0_raw_verdict": t0.get("p0_raw_verdict"),
                "semantic_gate": t0.get("semantic_gate"),
                "tags": (text.get("semantic_analysis") or {}).get("tags"),
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

    deltas = [r["delta_phi"] for r in rows]
    soften_text = sum(1 for r in rows if r["text"]["verdict"] == "SOFTEN")
    payload = {
        "signature": "Δ9Φ963-TWIN-GATE-CALIBRATION-v2",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "text_soften_count": soften_text,
            "mean_delta_phi": round(sum(deltas) / max(1, len(deltas)), 4),
            "max_delta_phi": max(deltas) if deltas else 0,
        },
        "scenarios": rows,
    }
    print(f"SUMMARY: text SOFTEN {soften_text}/{len(rows)} | mean Δφ={payload['summary']['mean_delta_phi']}")
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())