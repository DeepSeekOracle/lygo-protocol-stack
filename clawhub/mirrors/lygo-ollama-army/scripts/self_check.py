#!/usr/bin/env python3
"""Army skill self-check — policy clamps + import smoke (no autonomous loop)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ollama_command_center" / "scripts"))


def main() -> int:
    report: dict = {"ok": True, "checks": {}}

    # 1) SKILL frontmatter honesty markers
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8", errors="replace")
    for needle in (
        "0.8.1",
        "start_army_full_capacity.ps1",
        "LYGO_ARMY_I_CONSENT",
        "localhost",
        "auto_enable_planting",
        "process spawn",
    ):
        report["checks"][f"skill_has_{needle[:24]}"] = needle.lower() in skill.lower() or needle in skill

    # 2) Supervisor dual gate
    sup = (ROOT / "ollama_command_center" / "scripts" / "army_autonomous_supervisor.py").read_text(
        encoding="utf-8", errors="replace"
    )
    report["checks"]["supervisor_dual_gate"] = (
        "LYGO_ARMY_AUTONOMOUS" in sup and "LYGO_ARMY_I_CONSENT" in sup
    )
    report["checks"]["supervisor_no_popen"] = (
        "import subprocess" not in sup and "subprocess.Popen" not in sup and "Popen(" not in sup
    )

    # 3) self_tune refuses auto plant
    st = (ROOT / "ollama_command_center" / "scripts" / "army_self_tune.py").read_text(
        encoding="utf-8", errors="replace"
    )
    report["checks"]["self_tune_refuses_auto_plant"] = (
        "auto_enable_planting" in st
        and "Never auto-enable planting" in st
        or "forced_auto_enable_planting" in st
        or "NEVER auto-enable planting" in st
        or "never auto-enable planting" in st.lower()
    )
    report["checks"]["self_tune_mutating_doc"] = "MUTATING" in st or "mutating" in st

    # 4) PS1 spawn warning + gates
    ps1 = (ROOT / "start_army_full_capacity.ps1").read_text(encoding="utf-8", errors="replace")
    report["checks"]["ps1_spawn_warning"] = "SPAWN" in ps1.upper() or "SPAWNS" in ps1
    report["checks"]["ps1_triple_gate"] = all(
        x in ps1 for x in ("LYGO_ARMY_FULL_CAPACITY", "LYGO_ARMY_AUTONOMOUS", "LYGO_ARMY_I_CONSENT")
    )

    # 5) Genesis browser default off
    gen = (ROOT / "genesis_console" / "server.py").read_text(encoding="utf-8", errors="replace")
    report["checks"]["browser_gated"] = "LYGO_GENESIS_OPEN_BROWSER" in gen

    # 6) Supervisor refuses without env
    old = os.environ.pop("LYGO_ARMY_AUTONOMOUS", None)
    old2 = os.environ.pop("LYGO_ARMY_I_CONSENT", None)
    try:
        import army_autonomous_supervisor as aas  # noqa: E402

        rc = aas.main()
        report["checks"]["supervisor_refuses_without_env"] = rc == 2
    except Exception as e:
        report["checks"]["supervisor_refuses_without_env"] = False
        report["supervisor_err"] = str(e)[:120]
    finally:
        if old is not None:
            os.environ["LYGO_ARMY_AUTONOMOUS"] = old
        if old2 is not None:
            os.environ["LYGO_ARMY_I_CONSENT"] = old2

    report["ok"] = all(bool(v) for k, v in report["checks"].items() if k != "ok")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
