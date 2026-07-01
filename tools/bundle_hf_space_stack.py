#!/usr/bin/env python3
"""Bundle minimal P0–P5 stack into Hugging Face Space folder (no mirrors/rust target)."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HF = Path(__file__).resolve().parents[1].parent / "Hugging face"
DEST = HF / "protocol_stack"

INCLUDE_DIRS = [
    "stack",
    "protocol0_nano_kernel/src/python",
    "protocol0_nano_kernel/fixtures",
    "protocol1_memory_mycelium/src/python",
    "protocol2_cognitive_bridge/src/python",
    "protocol3_vortex_consensus/src/python",
    "protocol4_ascension_engine/src/python",
    "protocol5_harmony_node/src/python",
]

INCLUDE_FILES = [
    "tests/test_falsifiable_vectors.json",
    "tools/run_grok_audit_demo.py",
    "tools/generate_falsifiable_vectors.py",
]

TWIN_GATE_FILES = [
    "tests/pilot_edge_scenarios.json",
    "tests/twin_gate_calibration_last_run.json",
    "tests/twin_gate_vector_suite_last_run.json",
    "tools/run_twin_gate_calibration.py",
    "tools/run_twin_gate_vector_suite.py",
]

SKIP = {".git", "__pycache__", "target", ".pyc"}


def copy_rel(rel: str) -> None:
    src = REPO / rel
    if not src.exists():
        return
    dst = DEST / rel
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return
    for item in src.rglob("*"):
        if not item.is_file():
            continue
        if any(s in item.parts for s in SKIP) or item.suffix == ".pyc":
            continue
        out = DEST / item.relative_to(REPO)
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bundle protocol stack into HF Space folder")
    parser.add_argument("--mode", default="default", choices=("default", "twin-gate"))
    args = parser.parse_args()

    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)
    for rel in INCLUDE_DIRS:
        copy_rel(rel)
    for rel in INCLUDE_FILES:
        copy_rel(rel)
    if args.mode == "twin-gate":
        for rel in TWIN_GATE_FILES:
            copy_rel(rel)
        (DEST / "TWIN_GATE_MODE.txt").write_text("Δ9Φ963-TWIN-GATE-PHASE3-v1\n", encoding="utf-8")
        version = "Δ9Φ963-HF-STACK-BUNDLE-TWIN-GATE-v3.0\n"
    else:
        version = "Δ9Φ963-HF-STACK-BUNDLE-v2.0\n"
    (DEST / "BUNDLE_VERSION.txt").write_text(version, encoding="utf-8")
    print(f"Bundled stack → {DEST} (mode={args.mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())