#!/usr/bin/env python3
"""
Ops Detector evaluation — public, independent, dynamic metrics.

Usage:
  python eval_ops_detector.py [path/to/labeled_discourse_suite.json]
  python eval_ops_detector.py --threshold 0.15
  python eval_ops_detector.py --sweep

Writes tests/last_eval_report.json (next to suite) with precision/recall/FPR/AUC.
Stdlib only (no sklearn).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import lygo_ops_detector as det  # noqa: E402

DEFAULT_SUITE = ROOT / "tests" / "labeled_discourse_suite.json"
DEFAULT_OUT = ROOT / "tests" / "last_eval_report.json"


def load_suite(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    samples = data.get("samples") or data
    if not isinstance(samples, list):
        raise ValueError("suite must contain samples[]")
    return samples


def predict_binary(report: det.OpsReport, threshold: float) -> int:
    """1 = ops-positive. Prefer ops_score; also fire if evasion is Active."""
    if report.evasion_index > det.EVASION_ACTIVE_THRESHOLD:
        return 1
    return 1 if report.ops_score >= threshold else 0


def precision_recall_fpr(y_true: list[int], y_pred: list[int]) -> dict[str, float]:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "false_positive_rate": round(fpr, 4),
        "f1": round(f1, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }


def roc_auc(y_true: list[int], scores: list[float]) -> float:
    """Mann–Whitney / rank AUC (equivalent to ROC-AUC for binary labels)."""
    pos = [s for t, s in zip(y_true, scores) if t == 1]
    neg = [s for t, s in zip(y_true, scores) if t == 0]
    if not pos or not neg:
        return 0.0
    # Handle ties: average rank contribution
    greater = 0.0
    for p in pos:
        for n in neg:
            if p > n:
                greater += 1.0
            elif p == n:
                greater += 0.5
    return round(greater / (len(pos) * len(neg)), 4)


def evaluate(samples: list[dict], threshold: float) -> dict[str, Any]:
    y_true: list[int] = []
    y_pred: list[int] = []
    y_scores: list[float] = []
    rows: list[dict] = []

    for sample in samples:
        text = sample.get("text") or ""
        label = int(sample.get("label", 0))
        report = det.analyze(text=text, notes=f"eval:{sample.get('id', '')}")
        pred = predict_binary(report, threshold)
        score = float(report.ops_score)
        y_true.append(label)
        y_pred.append(pred)
        y_scores.append(score)
        rows.append(
            {
                "id": sample.get("id", "unknown"),
                "text": text[:120],
                "label": label,
                "predicted": pred,
                "ops_score": score,
                "evasion_index": report.evasion_index,
                "verdict": report.overall_verdict,
            }
        )

    metrics = precision_recall_fpr(y_true, y_pred)
    auc = roc_auc(y_true, y_scores)
    return {
        "suite_size": len(samples),
        "threshold_ops_score": threshold,
        "prediction_rule": (
            f"predicted=1 if evasion_index>{det.EVASION_ACTIVE_THRESHOLD} "
            f"OR ops_score>={threshold}"
        ),
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "false_positive_rate": metrics["false_positive_rate"],
        "f1": metrics["f1"],
        "auc": auc,
        "confusion": {k: metrics[k] for k in ("tp", "fp", "fn", "tn")},
        "results": rows,
        "generator": "scripts/eval_ops_detector.py",
        "detector_module": "scripts/lygo_ops_detector.py",
        "note": (
            "Metrics computed on the public labeled suite at the stated threshold. "
            "Not a claim of production harm/ethics calibration. Re-run after pattern changes."
        ),
    }


def sweep_thresholds(samples: list[dict], grid: list[float] | None = None) -> dict[str, Any]:
    grid = grid or [round(x * 0.05, 2) for x in range(0, 21)]
    best = None
    table = []
    for thr in grid:
        rep = evaluate(samples, thr)
        row = {
            "threshold": thr,
            "precision": rep["precision"],
            "recall": rep["recall"],
            "f1": rep["f1"],
            "fpr": rep["false_positive_rate"],
            "auc": rep["auc"],
        }
        table.append(row)
        if best is None or row["f1"] > best["f1"]:
            best = row
    return {"sweep": table, "best_f1_threshold": best}


def main() -> int:
    ap = argparse.ArgumentParser(description="Evaluate lygo-ops-detector on public labeled suite")
    ap.add_argument(
        "suite",
        nargs="?",
        default=str(DEFAULT_SUITE),
        help="Path to labeled_discourse_suite.json",
    )
    ap.add_argument(
        "--threshold",
        type=float,
        default=0.05,
        help="ops_score threshold for binary prediction on short discourse suite (use --sweep; 0.65 is strong multi-signal bar)",
    )
    ap.add_argument(
        "--doc-threshold",
        type=float,
        default=0.65,
        help="Also report metrics at documented 'strong pattern' ops threshold",
    )
    ap.add_argument("--sweep", action="store_true", help="Sweep thresholds 0.00–1.00")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="Write JSON report path")
    args = ap.parse_args()

    suite_path = Path(args.suite)
    if not suite_path.is_file():
        print(f"MISSING suite: {suite_path}", file=sys.stderr)
        return 2

    samples = load_suite(suite_path)
    report = evaluate(samples, args.threshold)
    report["at_documented_ops_threshold"] = evaluate(samples, args.doc_threshold)
    report["at_documented_ops_threshold"]["threshold_ops_score"] = args.doc_threshold
    # strip nested results to keep report smaller
    report["at_documented_ops_threshold"].pop("results", None)

    if args.sweep:
        report["threshold_sweep"] = sweep_thresholds(samples)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "precision": report["precision"],
                "recall": report["recall"],
                "false_positive_rate": report["false_positive_rate"],
                "f1": report["f1"],
                "auc": report["auc"],
                "threshold_ops_score": report["threshold_ops_score"],
                "suite_size": report["suite_size"],
                "at_documented_0.65": {
                    k: report["at_documented_ops_threshold"][k]
                    for k in ("precision", "recall", "false_positive_rate", "f1", "auc")
                },
                "best_f1_threshold": (report.get("threshold_sweep") or {}).get("best_f1_threshold"),
                "report": str(out_path),
            },
            indent=2,
        )
    )
    print(f"\nFull report written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
