#!/usr/bin/env python3
"""Upload haven star chart JSON to HF dataset (mirror for agents / Spaces)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "haven_star_chart"
DATA = OUT_DIR / "haven_star_chart_data.json"
META = OUT_DIR / "haven_star_chart_meta.json"
QUEUE = OUT_DIR / "haven_star_chart_queue.json"
REPO_ID = "DeepSeekOracle/lygo-protocol-stack"

UPLOADS = (
    ("haven_star_chart/haven_star_chart_data.json", DATA),
    ("haven_star_chart/haven_star_chart_meta.json", META),
    ("haven_star_chart/haven_star_chart_queue.json", QUEUE),
)


def main() -> int:
    if not DATA.is_file():
        print("Missing data — run tools/build_haven_star_chart.py", file=sys.stderr)
        return 2

    for rel, src in UPLOADS:
        if not src.is_file():
            print(f"Skip missing {src.name}", file=sys.stderr)
            continue
        cp = subprocess.run(
            ["hf", "upload", REPO_ID, str(src), rel, "--repo-type", "dataset"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if cp.returncode != 0:
            print(cp.stderr or cp.stdout, file=sys.stderr)
            print(
                json.dumps(
                    {
                        "ok": False,
                        "hint": "pip install huggingface_hub && hf auth login",
                        "local_path": str(src),
                        "dataset_path": rel,
                    }
                )
            )
            return 1
        print(f"Uploaded {rel}")

    print(json.dumps({"ok": True, "repo": REPO_ID, "files": [r for r, _ in UPLOADS]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())