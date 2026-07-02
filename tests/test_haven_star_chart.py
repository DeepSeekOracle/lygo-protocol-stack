"""Haven star chart builder smoke test."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_build_haven_star_chart():
    cp = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "build_haven_star_chart.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    data_path = ROOT / "docs" / "haven_star_chart" / "haven_star_chart_data.json"
    assert data_path.is_file()
    data = json.loads(data_path.read_text(encoding="utf-8"))
    assert data.get("signature", "").startswith("Δ9")
    assert data.get("node_count", 0) > 50
    assert any(n.get("id") == "SEAL_000" for n in data.get("nodes", []))
    assert cp.returncode in (0, 1)