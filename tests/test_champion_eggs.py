"""Champion kernel egg smoke tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_champion_registry_exists_and_count():
    reg = ROOT / "data" / "champion_eggs" / "registry.json"
    assert reg.is_file(), "run champion_egg_planter first"
    data = json.loads(reg.read_text(encoding="utf-8"))
    assert data.get("champion_count", 0) >= 15
    assert data.get("council_merkle_root")


def test_verify_champion_eggs_aligned():
    subprocess.run(
        [sys.executable, str(ROOT / "tools" / "verify_champion_eggs.py")],
        cwd=ROOT,
        check=True,
        timeout=120,
    )
    last = json.loads((ROOT / "tests" / "champion_eggs_last_run.json").read_text(encoding="utf-8"))
    assert last.get("all_pass") is True