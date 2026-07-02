#!/usr/bin/env python3
"""Upload haven star chart JSON to HF dataset (mirror for agents / Spaces)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "haven_star_chart" / "haven_star_chart_data.json"
META = ROOT / "docs" / "haven_star_chart" / "haven_star_chart_meta.json"
REPO_ID = "DeepSeekOracle/lygo-protocol-stack"


def main() -> int:
    if not DATA.is_file():
        print("Missing data — run tools/build_haven_star_chart.py", file=sys.stderr)
        return 2

    for rel in (
        "haven_star_chart/haven_star_chart_data.json",
        "haven_star_chart/haven_star_chart_meta.json",
    ):
        src = DATA if "data" in rel else META
        cp = subprocess.run(
            ["huggingface-cli", "upload", REPO_ID, str(src), rel, "--repo-type", "dataset"],
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
                        "hint": "pip install huggingface_hub && huggingface-cli login",
                        "local_path": str(src),
                        "dataset_path": rel,
                    }
                )
            )
            return 1
        print(f"Uploaded {rel}")

    print(json.dumps({"ok": True, "repo": REPO_ID}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())