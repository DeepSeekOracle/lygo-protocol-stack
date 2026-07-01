#!/usr/bin/env python3
"""Upload local Hugging face/ workspace to DeepSeekOracle/LYGO-Resonance-Engine Space."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SPACE_DIR = Path(__file__).resolve().parents[1].parent / "Hugging face"
REPO_ID = "DeepSeekOracle/LYGO-Resonance-Engine"


def main() -> int:
    parser = argparse.ArgumentParser(description="Push Hugging Face Space")
    parser.add_argument("--force-sync", action="store_true", help="Full tree upload (default hf upload)")
    parser.add_argument(
        "--message",
        default="Δ9Φ963: Twin Gate Phase 3 — text + byte vector (live P0-P5)",
    )
    args = parser.parse_args()

    if not (SPACE_DIR / "app.py").is_file():
        print(f"Missing app.py in {SPACE_DIR}", file=sys.stderr)
        return 1
    bundle = SPACE_DIR / "protocol_stack" / "stack" / "lygo_stack.py"
    if not bundle.is_file():
        print("Run: python tools/bundle_hf_space_stack.py --mode=twin-gate first", file=sys.stderr)
        return 1
    twin = SPACE_DIR / "protocol_stack" / "TWIN_GATE_MODE.txt"
    if not twin.is_file():
        print("Warning: TWIN_GATE_MODE.txt missing — run bundle with --mode=twin-gate", file=sys.stderr)

    cmd = [
        "hf",
        "upload",
        REPO_ID,
        str(SPACE_DIR),
        ".",
        "--repo-type",
        "space",
        "--commit-message",
        args.message,
    ]
    if args.force_sync:
        print("force-sync: uploading full Space directory")
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())