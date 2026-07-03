"""Resolve LYRA_CORE root for lyra-brain scripts."""
from __future__ import annotations

import os
from pathlib import Path


def lyra_core_root() -> Path:
    for key in ("LYRA_CORE_ROOT", "LYRA_CORE"):
        v = os.environ.get(key)
        if v:
            p = Path(v)
            if (p / "modules" / "lyra_brain.py").is_file():
                return p.resolve()
    candidates = [
        Path(r"I:\E Drive\LYRA_CORE"),
        Path.home() / "LYRA_CORE",
        Path(__file__).resolve().parents[3] / "LYRA_CORE",
    ]
    for p in candidates:
        if (p / "modules" / "lyra_brain.py").is_file():
            return p.resolve()
    raise RuntimeError(
        "LYRA_CORE not found. Set LYRA_CORE_ROOT to directory containing modules/lyra_brain.py"
    )