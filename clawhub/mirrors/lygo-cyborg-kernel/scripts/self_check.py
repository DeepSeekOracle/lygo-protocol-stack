#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cyborg_kernel as ck  # noqa: E402
import cyborg_task as ct  # noqa: E402


def main() -> int:
    boot = ck.boot_report()
    demo = __import__("continuum", fromlist=["cmd_demo"])
    sys.path.insert(0, str(ck.KERNEL))
    import continuum as cont  # noqa: E402

    d = cont.cmd_demo()
    # example task against skill root
    ex = {
        "goal": "self_check cyborg",
        "claims": [
            {"kind": "file_exists", "path": "SKILL.md"},
            {"kind": "file_contains", "path": "SKILL.md", "needle": "Cyborg"},
            {"kind": "file_exists", "path": "kernel/continuum.py"},
        ],
    }
    out = ct.run_task(ex, ck.SKILL, write_state=False, consent=False)
    src = (HERE / "cyborg_kernel.py").read_text(encoding="utf-8")
    no_sub = not re.search(r"(?m)^\s*import\s+subprocess\b", src)
    ok = (
        boot.get("ready")
        and d.get("ok")
        and out.get("can_claim_done")
        and no_sub
        and ck.VERSION == "1.0.0"
    )
    print(
        json.dumps(
            {
                "ok": ok,
                "signature": ck.SIG,
                "boot_ready": boot.get("ready"),
                "continuum_demo": d.get("ok"),
                "task_can_claim_done": out.get("can_claim_done"),
                "no_subprocess_import": no_sub,
            },
            indent=2,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
