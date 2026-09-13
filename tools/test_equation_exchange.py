#!/usr/bin/env python3
"""Assert the 2026-09-13 operators fire as specified. Exit 0 = proven this run."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools" / "run_equation_exchange.py"
JSON_OUT = ROOT / "docs" / "LYGO_EQUATION_EXCHANGE_RUN.json"


def main() -> int:
    r = subprocess.run([sys.executable, str(RUNNER)], cwd=str(ROOT), check=False)
    if r.returncode != 0:
        print("FAIL runner")
        return 1
    data = json.loads(JSON_OUT.read_text(encoding="utf-8"))
    runs = data["runs"]
    fails = []

    def need(cond: bool, msg: str) -> None:
        if not cond:
            fails.append(msg)

    q = runs["quiet"]
    need(q["finite"] and not q["P0"] and q["I_holds"] and q["W_holds"], "quiet must hold")
    g = runs["gaslight"]
    need(g["P0"] and g["finite"], "gaslight must P0 and stay finite")
    t = runs["two_truths"]
    need(t["P3_conflict"], "two_truths must P3")
    u = runs["unbound_Q"]
    need(u["P3_curiosity"] and u["finite"], "unbound_Q must P3 curiosity, finite")
    w = runs["weak_bond"]
    need((not w["I_holds"]) and (not w["W_holds"]), "weak_bond must fail I and W")
    if fails:
        print("FAIL", fails)
        return 1
    print("PASS equation-exchange v1 — five named gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
