#!/usr/bin/env python3
"""Stage lygo-protocol-stack (no .git/target/mirrors) and upload to HF dataset."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "_hf_staging"
REPO = "DeepSeekOracle/lygo-protocol-stack"
SKIP_DIRS = {".git", "target", "__pycache__", "_hf_staging", "mirrors"}
SKIP_SUFFIX = {".pyc"}


def copy_tree(src: Path, dst: Path) -> None:
    for item in src.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(src)
        if any(p in SKIP_DIRS for p in rel.parts):
            continue
        if len(rel.parts) >= 2 and rel.parts[0] == "clawhub" and rel.parts[1] == "mirrors":
            continue
        if item.suffix in SKIP_SUFFIX:
            continue
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, out)


def main() -> int:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir()
    copy_tree(ROOT, STAGE)
    hf_readme = ROOT / "README_HF.md"
    if hf_readme.is_file():
        shutil.copy2(hf_readme, STAGE / "README.md")
    cmd = [
        "hf",
        "upload",
        REPO,
        str(STAGE),
        ".",
        "--repo-type",
        "dataset",
        "--commit-message",
        "Δ9Φ963 2026-07-04: lygo-champion-lightfather, Biophase7 deadman seed, protocol9_failsafe, sovereign+LF vector v1.1",
    ]
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())