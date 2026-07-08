#!/usr/bin/env python3
"""Phase-2 pilot: real-world ethical edge cases through live process_ethical_query (no mocks)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stack"))

from lygo_stack import deploy_stack  # noqa: E402

DEFAULT = ROOT / "tests" / "pilot_edge_scenarios.json"
SIGNATURE = "Δ9Φ963-PILOT-PHASE2-v1"


def run_pilot(path: Path, write_report: bool = True) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    stack = deploy_stack("PILOT_ETHICAL_GUARDIAN")
    results = {
        "signature": SIGNATURE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scenarios": [],
    }

    print("=" * 72)
    print(" LYGO ETHICAL GUARDIAN — PILOT PHASE 2 (live text P0-P5)")
    print(f" {SIGNATURE}")
    print("=" * 72)

    for sc in data.get("scenarios", []):
        q = sc.get("query", "").strip()
        sid = sc.get("id", "UNKNOWN")
        print(f"\n[{sid}] {sc.get('label', '')}")
        print(f"  Query: {q[:100]}{'…' if len(q) > 100 else ''}")

        sev = sc.get("severity")
        report = stack.process_ethical_query(
            q, severity=float(sev) if sev is not None else None, purpose=f"pilot_{sid}"
        )
        p0 = report.get("p0") or {}
        p3 = report.get("p3") or {}
        row = {
            "id": sid,
            "label": sc.get("label"),
            "query": q,
            "p0_verdict": p0.get("verdict"),
            "phi_risk": p0.get("phi_risk", p0.get("risk")),
            "p0_hash": p0.get("hash"),
            "p0_reasoning": (p0.get("reasoning") or "")[:300],
            "p3_consensus": p3.get("consensus_found"),
            "harmonic_center": p3.get("harmonic_center", p3.get("consensus")),
            "light_code": report.get("light_code"),
            "ethical_mass": report.get("ethical_mass"),
            "stack_version": report.get("stack_version"),
            "resonance_signature": report.get("resonance_signature"),
        }
        p4 = report.get("p4") or {}
        row["p4_repair"] = not p4.get("skipped", True)
        results["scenarios"].append(row)

        print(f"  -> P0: {row['p0_verdict']} | phi_risk: {row['phi_risk']}")
        print(f"  -> P0 hash: {row['p0_hash']}")
        print(f"  -> P3 consensus: {row['p3_consensus']}")
        print(f"  -> P4 repair: {row['p4_repair']}")
        print(f"  -> Light Code: {row['light_code']}")
        print(f"  -> Ethical mass: {row['ethical_mass']}")

    print("\n" + "=" * 72)
    print(f" Scenarios run: {len(results['scenarios'])}")
    print("=" * 72)

    if write_report:
        out = ROOT / "tests" / "pilot_phase2_last_run.json"
        out.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"Report: {out}")

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Pilot phase-2 edge scenarios")
    parser.add_argument("--scenarios", type=Path, default=DEFAULT)
    parser.add_argument("--no-report", action="store_true")
    args = parser.parse_args()
    run_pilot(args.scenarios, write_report=not args.no_report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())