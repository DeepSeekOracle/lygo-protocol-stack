#!/usr/bin/env python3
"""Calibration harness for byte_entropy_filter.py (Biophase7 honest metrics)."""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / "protocol0_byte_entropy_filter" / "src" / "python"
sys.path.insert(0, str(PY))

from byte_entropy_filter import validate_bytes  # noqa: E402


def load_dataset(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        payload = json.load(f)
    return payload.get("vectors") or payload.get("samples") or []


def calibrate(dataset_path: str, report_path: str) -> dict:
    vectors = load_dataset(Path(dataset_path))

    by_category: dict[str, list[dict]] = defaultdict(list)
    per_vector_results = []

    for v in vectors:
        if "hex" in v:
            data = bytes.fromhex(v["hex"])
        elif v.get("generate") == "zeros":
            data = b"\x00" * int(v["length"])
        else:
            continue
        result = validate_bytes(data)
        row = {
            "id": v["id"],
            "category": v.get("category", v.get("label", "unknown")),
            "len": len(data),
            "verdict": result["verdict"],
            "entropy": result["entropy"],
            "compression": result["compression"],
            "score": result.get("score", result.get("phi_risk")),
        }
        per_vector_results.append(row)
        by_category[row["category"]].append(row)

    category_summary = {}
    for cat, rows in by_category.items():
        entropies = [r["entropy"] for r in rows]
        comps = [r["compression"] for r in rows]
        verdict_counts = defaultdict(int)
        for r in rows:
            verdict_counts[r["verdict"]] += 1
        category_summary[cat] = {
            "n": len(rows),
            "entropy_mean": round(statistics.mean(entropies), 4),
            "entropy_stdev": round(statistics.pstdev(entropies), 4) if len(entropies) > 1 else 0.0,
            "compression_mean": round(statistics.mean(comps), 4),
            "verdict_counts": dict(verdict_counts),
        }

    nl = category_summary.get("natural_language", {}).get("entropy_mean")
    rb = category_summary.get("random_bytes", {}).get("entropy_mean")
    separation_note = (
        f"natural_language mean entropy={nl}, random_bytes mean entropy={rb}. "
        + (
            "WARNING: overlap — filter may not distinguish text from noise."
            if nl is not None and rb is not None and abs(nl - rb) < 0.1
            else "Separated as expected."
        )
    )

    report = {
        "per_vector": per_vector_results,
        "by_category": category_summary,
        "separation_check": separation_note,
        "scope_note": (
            "This report measures byte-statistic separation between data shapes. "
            "It is not a harm/ethics calibration and should not be cited as one."
        ),
    }

    Path(report_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    dataset = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "tests" / "calibration_dataset.json")
    out = sys.argv[2] if len(sys.argv) > 2 else str(ROOT / "tests" / "calibration_report.json")
    rep = calibrate(dataset, out)
    print(json.dumps(rep["by_category"], indent=2))
    print(rep["separation_check"])
    print(f"\nFull report written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())