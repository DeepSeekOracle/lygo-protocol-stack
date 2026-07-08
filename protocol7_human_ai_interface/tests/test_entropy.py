from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from protocol7_human_ai_interface.entropy_extraction import extract_p0_seed_from_ibi


def test_ibi_seed():
    ibi = [800 + i * 3.5 for i in range(20)]
    out = extract_p0_seed_from_ibi(ibi)
    assert len(out["seed_256"]) == 64
    assert out["ibi_count"] == 20