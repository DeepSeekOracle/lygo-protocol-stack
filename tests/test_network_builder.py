"""Network builder anchors + verify script."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANCHORS = ROOT / "docs" / "network_builder" / "IMMUTABLE_ANCHORS.json"


def test_immutable_anchors_json_loads():
    data = json.loads(ANCHORS.read_text(encoding="utf-8"))
    assert data["skill_slug"] == "lygo-network-builder"
    chants = data.get("traversal_chants") or []
    assert len(chants) >= 4
    groups = data.get("immutable_anchors") or {}
    assert "physics" in groups and "sovereign_seed" in groups


def test_verify_script_writes_last_run():
    cp = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "lygo_network_builder_verify.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )
    out = ROOT / "tests" / "network_builder_last_run.json"
    assert out.is_file()
    report = json.loads(out.read_text(encoding="utf-8"))
    assert "anchors_sha256" in report
    assert "vectors" in report
    assert report.get("signature", "").startswith("Δ9")
    # HTTP may fail in CI without network; local_repo rows must pass
    local_rows = [v for v in report["vectors"] if v.get("mode") == "local_repo"]
    assert all(v.get("ok") for v in local_rows)
    assert cp.returncode in (0, 1)