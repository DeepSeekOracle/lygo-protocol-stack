#!/usr/bin/env python3
"""
LYGO PROTOCOL STACK - GROK AUDIT HARNESS (P1-P5)
Version: GROK-AUDIT-HARNESS-v2

Runs 40+ falsifiable vectors through live deploy_stack() / process_falsifiable_vector().
No mock phi_risk or post-hoc verdict overrides.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stack"))

from lygo_stack import deploy_stack  # noqa: E402

DEFAULT_VECTORS = ROOT / "tests" / "test_falsifiable_vectors.json"
SIGNATURE = "GROK-AUDIT-HARNESS-v2"


def run_audit_demo(vector_path: Path, *, limit: int | None = None, write_report: bool = True) -> dict:
    if not vector_path.is_file():
        raise FileNotFoundError(
            f"Missing {vector_path}. Run: python tools/generate_falsifiable_vectors.py"
        )

    data = json.loads(vector_path.read_text(encoding="utf-8"))
    stack = deploy_stack("GROK_AUDIT_HARNESS")

    print("=" * 70)
    print(" LYGO PROTOCOL STACK - GROK AUDIT HARNESS")
    print("   Live P0-P5 ? Primordial Law + Layer 1 Sovereignty enforced")
    print(f"   {SIGNATURE}")
    print("=" * 70 + "\n")

    results = {
        "signature": SIGNATURE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "vector_file_version": data.get("version"),
        "total_vectors": 0,
        "passed": 0,
        "failed": 0,
        "details": [],
    }

    count = 0
    for category, vectors in (data.get("categories") or {}).items():
        print(f" Category: {category.upper()}")
        print("-" * 70)
        for vec in vectors:
            if limit is not None and count >= limit:
                break
            count += 1
            results["total_vectors"] += 1
            claim = (vec.get("payload") or {}).get("claim", "N/A")
            print(f"\n[*] Vector: {vec.get('id')}")
            print(f"    Claim: {str(claim)[:100]}{'...' if len(str(claim)) > 100 else ''}")

            try:
                live = stack.process_falsifiable_vector(vec, category=category)
                decision = live["decision"]
                expected = str(vec.get("expected_decision", "UNKNOWN")).upper()
                passed = decision == expected
                if passed:
                    results["passed"] += 1
                else:
                    results["failed"] += 1

                row = {
                    "id": vec.get("id"),
                    "category": category,
                    "decision": decision,
                    "expected": expected,
                    "phi_risk": round(float(live.get("phi_risk", 0)), 4),
                    "passed": passed,
                    "p0_hash": live.get("p0_hash"),
                    "gate_len": live.get("gate_len"),
                    "light_code": live.get("light_code"),
                    "repair_triggered": live.get("repair_triggered"),
                    "ethical_mass": live.get("ethical_mass"),
                    "design_reasoning": vec.get("expected_reasoning"),
                    "live_reasoning": (live.get("reasoning") or "")[:240],
                }
                results["details"].append(row)

                status = "PASS" if passed else "FAIL"
                print(f"    -> phi_risk: {row['phi_risk']:.4f}")
                print(f"    -> decision: {decision} (expected: {expected})")
                print(f"    -> P0 hash: {row.get('p0_hash')} | gate_len: {row.get('gate_len')}")
                print(f"    -> P4 repair: {row.get('repair_triggered')}")
                print(f"    -> Light Code: {live.get('light_code')}")
                print(f"    -> status: {status}")
            except Exception as exc:
                results["failed"] += 1
                print(f"    ERROR: {exc}")
                results["details"].append(
                    {"id": vec.get("id"), "category": category, "passed": False, "error": str(exc)}
                )
        if limit is not None and count >= limit:
            break

    total = max(results["total_vectors"], 1)
    rate = 100.0 * results["passed"] / total
    print("\n" + "=" * 70)
    print(" AUDIT SUMMARY")
    print("=" * 70)
    print(f"    Total Vectors: {results['total_vectors']}")
    print(f"    Passed: {results['passed']}")
    print(f"    Failed: {results['failed']}")
    print(f"    Pass Rate: {rate:.1f}%")
    print("=" * 70)

    if write_report:
        report_path = ROOT / "tests" / "grok_audit_last_run.json"
        report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"Report: {report_path}")

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Grok audit harness (live stack)")
    parser.add_argument("--vectors", type=Path, default=DEFAULT_VECTORS)
    parser.add_argument("--limit", type=int, default=None, help="Run first N vectors only")
    parser.add_argument("--no-report", action="store_true")
    args = parser.parse_args()
    results = run_audit_demo(args.vectors, limit=args.limit, write_report=not args.no_report)
    return 0 if results.get("failed", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())