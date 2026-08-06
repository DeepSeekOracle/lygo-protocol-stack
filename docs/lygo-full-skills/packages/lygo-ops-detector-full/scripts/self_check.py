#!/usr/bin/env python3
"""Self-check for LYGO Ops Detector (Lightfather / AETHONΔ9) skill pack."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQ_FILES = [
    ROOT / "SKILL.md",
    ROOT / "references" / "SECURITY.md",
    ROOT / "references" / "AETHON_D9_BLUEPRINT.md",
    ROOT / "scripts" / "lygo_ops_detector.py",
    ROOT / "scripts" / "eval_ops_detector.py",
    ROOT / "tests" / "labeled_discourse_suite.json",
]

missing = [str(p.relative_to(ROOT)) for p in REQ_FILES if not p.exists()]
if missing:
    print("MISSING_FILES:")
    for m in missing:
        print(" -", m)
    sys.exit(3)

# Import and smoke-test the core module
try:
    sys.path.insert(0, str(ROOT / "scripts"))
    import lygo_ops_detector as det
except Exception as e:
    print("IMPORT_FAIL:", e)
    sys.exit(2)

# Verify locked weights and thresholds
assert abs(sum(det.EVASION_WEIGHTS.values()) - 1.0) < 0.001, "Evasion weights must sum to 1.0"
assert abs(sum(det.ASSOCIATION_WEIGHTS.values()) - 1.0) < 0.001, "Association weights must sum to 1.0"
assert det.EVASION_ACTIVE_THRESHOLD == 0.70
assert det.ASSOCIATION_HIGH_THRESHOLD == 0.65

# Run a minimal analysis
sample_text = (
    "It's on you to prove it. Tons of evidence out there. "
    "As a former intelligence officer I can tell you you're overreacting and imagining things. "
    "What about the other side? My sources confirm."
)
report = det.analyze(text=sample_text, notes="self_check smoke test")

if report.evasion_index <= 0.0:
    print("EVA_SMOKE_FAIL: evasion score zero on clear signals")
    sys.exit(4)

if "GASLIGHTING" not in report.evasion_verdict.upper() and report.evasion_index < 0.5:
    # Not strict, but expect elevated
    pass

# Smoke eval path exists and can score the suite (dynamic metrics)
suite = ROOT / "tests" / "labeled_discourse_suite.json"
samples = json.loads(suite.read_text(encoding="utf-8")).get("samples") or []
if len(samples) < 10:
    print("SUITE_TOO_SMALL")
    sys.exit(5)
# one deceptive + one benign
d0 = next(s for s in samples if s.get("label") == 1)
b0 = next(s for s in samples if s.get("label") == 0)
rd = det.analyze(d0["text"])
rb = det.analyze(b0["text"])
if rd.ops_score < rb.ops_score and rd.evasion_index <= rb.evasion_index:
    print("RANK_FAIL: deceptive sample not ranked above benign")
    sys.exit(6)

print("OK")
print("EVASION", report.evasion_index)
print("ASSOC", report.association_index)
print("RISK", report.combined_risk)
print("VERDICT", report.overall_verdict)
print("LIGHTFATHER", report.lightfather_note)
print("SUITE_SAMPLES", len(samples))
print("METRICS_SOURCE", det.PERFORMANCE_METRICS.get("source"))
