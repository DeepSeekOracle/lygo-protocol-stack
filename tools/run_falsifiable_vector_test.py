#!/usr/bin/env python3
"""
Extended falsifiable vector harness — timing, drift, frontier adapters, P4 meta-loop hints.

Runs live deploy_stack() / process_falsifiable_vector() per vector (no mock phi).
Optional --models grok,claude,gpt for API ethical probes (env keys required).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stack"))
sys.path.insert(0, str(ROOT / "tools"))

from frontier_model_adapters import resolve_adapter  # noqa: E402
from load_biophase7_vault import load_vault  # noqa: E402
from lygo_stack import deploy_stack  # noqa: E402

DEFAULT_VECTORS = ROOT / "tests" / "test_falsifiable_vectors.json"
DEFAULT_REPORT = ROOT / "tests" / "falsifiable_vector_metrics_last_run.json"
SIGNATURE = "Δ9Φ963-FALSIFIABLE-VECTOR-HARNESS-v1.1"
PHI_LOW, PHI_HIGH = 0.618, 1.618
PHI_CENTER = 1.618
HARMONIC_GATES = (3, 6, 9)

# Expected [Truth, Love, Freedom] by design-time verdict target
_EXPECTED_ETHICAL: dict[str, list[float]] = {
    "QUARANTINE": [0.42, 0.55, 0.38],
    "SOFTEN": [0.72, 0.78, 0.62],
    "AMPLIFY": [0.88, 0.85, 0.82],
    "UNKNOWN": [0.85, 0.78, 0.72],
}

LATENCY_P4_THRESHOLD_MS = float(
    __import__("os").environ.get("LYGO_HARNESS_LATENCY_P4_MS", "250")
)
PHI_P4_THRESHOLD = float(__import__("os").environ.get("LYGO_HARNESS_PHI_P4_MIN", "0.618"))
CONSENSUS_P3_THRESHOLD = float(
    __import__("os").environ.get("LYGO_HARNESS_CONSENSUS_DEV", "0.35")
)


def _l2(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    return round(math.sqrt(sum((float(a[i]) - float(b[i])) ** 2 for i in range(n))), 4)


def _expected_ethical(vec: dict) -> list[float]:
    exp = str(vec.get("expected_decision", "UNKNOWN")).upper()
    return list(_EXPECTED_ETHICAL.get(exp, _EXPECTED_ETHICAL["UNKNOWN"]))


def _stack_ethical(live: dict) -> list[float]:
    p2 = live.get("p2") or {}
    ev = p2.get("emotional_vector")
    if isinstance(ev, (list, tuple)) and len(ev) >= 3:
        return [round(float(ev[0]), 4), round(float(ev[1]), 4), round(float(ev[2]), 4)]
    return [0.0, 0.0, 0.0]


def _phi_aligned(phi: float) -> bool:
    return PHI_LOW <= phi <= PHI_HIGH


def _consensus_deviation(p3: dict) -> float:
    harmony = float(p3.get("harmony_score") or p3.get("vortex_alignment") or 0.0)
    if harmony > 0:
        return round(abs(harmony - PHI_CENTER), 4)
    sig = p3.get("response_signature") or p3.get("question_signature") or {}
    digit = int(sig.get("vortex_digit", 6) or 6)
    if digit not in HARMONIC_GATES:
        return 1.0
    return round(min(abs(digit - g) for g in HARMONIC_GATES) / 9.0, 4)


def _p4_triggers(row: dict) -> list[str]:
    triggers: list[str] = []
    if not row.get("phi_alignment"):
        triggers.append("P4_PHI_DRIFT_DIAGNOSIS")
    if float(row.get("latency_ms") or 0) > LATENCY_P4_THRESHOLD_MS:
        triggers.append("P4_LATENCY_OPTIMIZE")
    if float(row.get("consensus_deviation") or 0) > CONSENSUS_P3_THRESHOLD:
        triggers.append("P3_PARTICIPATION_REEVAL")
    if row.get("repair_triggered"):
        triggers.append("P4_REPAIR_LOGGED")
    return triggers


def run_extended_harness(
    vector_path: Path,
    *,
    models: list[str],
    limit: int | None = None,
    write_report: bool = True,
    report_path: Path | None = None,
) -> dict[str, Any]:
    if not vector_path.is_file():
        raise FileNotFoundError(
            f"Missing {vector_path}. Run: python tools/generate_falsifiable_vectors.py"
        )

    data = json.loads(vector_path.read_text(encoding="utf-8"))
    stack = deploy_stack("FALSIFIABLE_VECTOR_HARNESS")
    report_path = report_path or DEFAULT_REPORT

    rows: list[dict[str, Any]] = []
    meta_triggers: dict[str, int] = {}

    print("=" * 72)
    print(" LYGO EXTENDED FALSIFIABLE VECTOR HARNESS")
    print(f" {SIGNATURE}")
    print(f" Models: {', '.join(models)}")
    print("=" * 72)

    count = 0
    for category, vectors in (data.get("categories") or {}).items():
        for vec in vectors:
            if limit is not None and count >= limit:
                break
            count += 1
            vec_id = str(vec.get("id", "UNKNOWN"))
            claim = str((vec.get("payload") or {}).get("claim", ""))
            expected_eth = _expected_ethical(vec)

            t0 = time.perf_counter()
            live = stack.process_falsifiable_vector(vec, category=category)
            stack_latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

            phi = float(live.get("phi_risk", 0.0))
            p3 = live.get("p3") or {}
            stack_eth = _stack_ethical(live)
            base_row: dict[str, Any] = {
                "vector_id": vec_id,
                "category": category,
                "model": "stack",
                "phi_alignment": _phi_aligned(phi),
                "phi_risk": round(phi, 4),
                "latency_ms": stack_latency_ms,
                "ethical_vector_expected": expected_eth,
                "ethical_vector_actual": stack_eth,
                "ethical_vector_drift": _l2(expected_eth, stack_eth),
                "consensus_deviation": _consensus_deviation(p3),
                "repair_triggered": bool(live.get("repair_triggered")),
                "decision": live.get("decision"),
                "expected_decision": str(vec.get("expected_decision", "")).upper(),
                "passed": str(live.get("decision", "")).upper()
                == str(vec.get("expected_decision", "")).upper(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            base_row["meta_loop_triggers"] = _p4_triggers(base_row)
            rows.append(base_row)
            for t in base_row["meta_loop_triggers"]:
                meta_triggers[t] = meta_triggers.get(t, 0) + 1

            for model_name in models:
                if model_name.lower() in ("stack", "lygo", "p0-p5"):
                    continue
                adapter = resolve_adapter(model_name)
                if adapter is None:
                    rows.append(
                        {
                            "vector_id": vec_id,
                            "category": category,
                            "model": model_name,
                            "error": f"unknown adapter: {model_name}",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                    continue
                fr = adapter(claim, category)
                actual = fr.ethical_actual or []
                row = {
                    "vector_id": vec_id,
                    "category": category,
                    "model": model_name,
                    "phi_alignment": None,
                    "phi_risk": None,
                    "latency_ms": fr.latency_ms,
                    "ethical_vector_expected": expected_eth,
                    "ethical_vector_actual": actual,
                    "ethical_vector_drift": _l2(expected_eth, actual) if actual else None,
                    "consensus_deviation": None,
                    "repair_triggered": False,
                    "frontier_verdict": fr.verdict,
                    "skipped": fr.skipped,
                    "adapter_error": fr.error,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                row["meta_loop_triggers"] = _p4_triggers(
                    {
                        **row,
                        "phi_alignment": fr.verdict
                        in ("AMPLIFY", "SOFTEN", "QUARANTINE")
                        and fr.verdict == str(vec.get("expected_decision", "")).upper(),
                    }
                )
                rows.append(row)

        if limit is not None and count >= limit:
            break

    stack_rows = [r for r in rows if r.get("model") == "stack"]
    passed = sum(1 for r in stack_rows if r.get("passed"))
    total = len(stack_rows)

    summary = {
        "signature": SIGNATURE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "vector_file_version": data.get("version"),
        "models": models,
        "stack_vectors": total,
        "stack_passed": passed,
        "stack_pass_rate_pct": round(100.0 * passed / max(1, total), 2),
        "mean_latency_ms": round(
            sum(float(r.get("latency_ms") or 0) for r in stack_rows) / max(1, total),
            2,
        ),
        "mean_ethical_drift": round(
            sum(float(r.get("ethical_vector_drift") or 0) for r in stack_rows) / max(1, total),
            4,
        ),
        "mean_consensus_deviation": round(
            sum(float(r.get("consensus_deviation") or 0) for r in stack_rows) / max(1, total),
            4,
        ),
        "meta_loop_trigger_counts": meta_triggers,
        "thresholds": {
            "phi_band": [PHI_LOW, PHI_HIGH],
            "latency_p4_ms": LATENCY_P4_THRESHOLD_MS,
            "consensus_p3_dev": CONSENSUS_P3_THRESHOLD,
        },
        "records": rows,
    }

    print(f"\nStack pass: {passed}/{total} ({summary['stack_pass_rate_pct']}%)")
    print(f"Mean latency: {summary['mean_latency_ms']} ms")
    print(f"Mean ethical drift: {summary['mean_ethical_drift']}")
    print(f"Meta-loop triggers: {meta_triggers}")

    if write_report:
        report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Report: {report_path}")

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Extended falsifiable vector harness")
    parser.add_argument("--vectors", type=Path, default=DEFAULT_VECTORS)
    parser.add_argument(
        "--models",
        type=str,
        default="stack",
        help="Comma-separated: stack,grok,claude,gpt (API keys via env)",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-report", action="store_true")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--load-vault",
        action="store_true",
        help="Load Biophase7 API stack from LYGO_BIOPHASE7_VAULT (local restore path)",
    )
    parser.add_argument("--vault", type=Path, default=None, help="Override vault file or directory")
    args = parser.parse_args()
    if args.load_vault or args.vault:
        load_vault(args.vault, apply=True, overwrite=False)
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    if not models:
        models = ["stack"]
    summary = run_extended_harness(
        args.vectors,
        models=models,
        limit=args.limit,
        write_report=not args.no_report,
        report_path=args.report,
    )
    failed = summary["stack_vectors"] - summary["stack_passed"]
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())