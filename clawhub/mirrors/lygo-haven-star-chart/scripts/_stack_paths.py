"""Resolve lygo-protocol-stack root for haven-star-chart scripts."""

from __future__ import annotations

import os
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]


def resolve_stack_root(explicit: str | None = None) -> Path:
    if explicit:
        p = Path(explicit).resolve()
        _assert_stack(p)
        return p
    env = os.environ.get("LYGO_STACK_ROOT", "").strip()
    if env:
        p = Path(env).resolve()
        _assert_stack(p)
        return p
    for anc in SKILL_ROOT.parents:
        if (anc / "tools" / "haven_star_chart_gate.py").is_file():
            _assert_stack(anc)
            return anc
    raise SystemExit("Set LYGO_STACK_ROOT to a lygo-protocol-stack clone")


def _assert_stack(p: Path) -> None:
    required = [
        p / "tools" / "haven_star_chart_gate.py",
        p / "tools" / "haven_star_chart_submit.py",
        p / "docs" / "haven_star_chart" / "AGENT_PORTAL.md",
        p / "docs" / "haven_star_chart" / "submission_schema.json",
    ]
    missing = [str(x.relative_to(p)) for x in required if not x.is_file()]
    if missing:
        raise SystemExit(f"Invalid stack root {p}; missing: {missing}")