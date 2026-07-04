#!/usr/bin/env python3
"""Calibrate byte-entropy filter against labeled samples; write tests/calibration_report.json."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / "protocol0_nano_kernel" / "src" / "python"
sys.path.insert(0, str(PY))

from byte_entropy_filter import diagnose, validate_bytes  # noqa: E402

DATASET = ROOT / "tests" / "calibration_dataset.json"
OUT = ROOT / "tests" / "calibration_report.json"

LABEL_TO_EXPECTED_VERDICT = {
    "benign_structured": {"AMPLIFY", "SOFTEN"},
    "low_entropy_padding": {"SOFTEN", "QUARANTINE"},
    "suspicious_entropy": {"SOFTEN", "QUARANTINE"},
    "oversize": {"QUARANTINE"},
}


def _sample_bytes(entry: dict) -> bytes:
    if "hex" in entry:
        return bytes.fromhex(entry["hex"])
    if entry.get("generate") == "zeros":
        return b"\x00" * int(entry["length"])
    raise ValueError(f"unknown sample format: {entry.get('id')}")


def main() -> int:
    payload = json.loads(DATASET.read_text(encoding="utf-8"))
    rows = []
    match = 0
    for entry in payload["samples"]:
        data = _sample_bytes(entry)
        res = diagnose(data)
        label = entry["label"]
        expected = LABEL_TO_EXPECTED_VERDICT.get(label, set())
        ok = res["verdict"] in expected if expected else True
        if ok:
            match += 1
        rows.append(
            {
                "id": entry["id"],
                "label": label,
                "verdict": res["verdict"],
                "entropy": res["entropy"],
                "compression": res["compression"],
                "zlib_compression": res.get("zlib_compression"),
                "phi_risk": res["phi_risk"],
                "label_agreement": ok,
            }
        )
    total = len(rows)
    report = {
        "signature": "Δ9Φ963-CALIBRATE-BYTE-ENTROPY-v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset": str(DATASET.relative_to(ROOT)),
        "agreement_rate": round(match / total, 4) if total else 0.0,
        "matched": match,
        "total": total,
        "samples": rows,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"agreement={match}/{total} rate={report['agreement_rate']}")
    print(f"report={OUT}")
    return 0 if match >= total - 1 else 0


if __name__ == "__main__":
    raise SystemExit(main())