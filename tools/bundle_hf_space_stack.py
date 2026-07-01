#!/usr/bin/env python3
"""Bundle minimal P0–P5 stack into Hugging Face Space folder (no mirrors/rust target)."""

from __future__ import annotations

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
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)
    for rel in INCLUDE_DIRS:
        copy_rel(rel)
    for rel in INCLUDE_FILES:
        copy_rel(rel)
    marker = DEST / "BUNDLE_VERSION.txt"
    marker.write_text("Δ9Φ963-HF-STACK-BUNDLE-v2.0\n", encoding="utf-8")
    print(f"Bundled stack → {DEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())