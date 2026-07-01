#!/usr/bin/env python3
"""Upload P0 hardening fixtures/manifest to HF dataset (public mirror)."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "DeepSeekOracle/lygo-protocol-stack"
FIX = ROOT / "protocol0_nano_kernel" / "fixtures"


def main() -> int:
    if not (FIX / "p0_vectors.json").is_file():
        print("Missing p0_vectors.json", file=sys.stderr)
        return 1
    stage = Path(tempfile.mkdtemp(prefix="lygo_p0_"))
    dest = stage / "protocol0_nano_kernel" / "fixtures"
    dest.mkdir(parents=True)
    for name in ("p0_vectors.json", "p0_vectors.tsv", "p0_canonical.sha256", "P0_VECTOR_MANIFEST.md"):
        src = FIX / name
        if src.is_file():
            shutil.copy2(src, dest / name)
    readme = stage / "README_P0_HARDENING.md"
    readme.write_text(
        "# P0 hardening mirror\n\nSynced from lygo-protocol-stack protocol0_nano_kernel/fixtures.\n",
        encoding="utf-8",
    )
    cmd = [
        "hf",
        "upload",
        REPO,
        str(stage),
        "protocol0_nano_kernel/fixtures",
        "--repo-type",
        "dataset",
        "--commit-message",
        "Δ9Φ963: P0 hardening manifest + vectors mirror",
    ]
    print("Running:", " ".join(cmd))
    rc = subprocess.call(cmd)
    shutil.rmtree(stage, ignore_errors=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())