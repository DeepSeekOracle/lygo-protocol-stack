#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "kernel"))
import continuum as cont  # noqa: E402
import cyborg_kernel as ck  # noqa: E402
import cyborg_task as ct  # noqa: E402
import lattice_net as net  # noqa: E402


def main() -> int:
    boot = ck.boot_report()
    d = cont.cmd_demo()
    ex = {
        "goal": "self_check cyborg",
        "claims": [
            {"kind": "file_exists", "path": "SKILL.md"},
            {"kind": "file_contains", "path": "SKILL.md", "needle": "Cyborg"},
            {"kind": "file_exists", "path": "kernel/continuum.py"},
            {"kind": "file_exists", "path": "kernel/lattice_net.py"},
        ],
    }
    out = ct.run_task(ex, ck.SKILL, write_state=False, consent=False)
    pulse = net.lattice_pulse()
    src = (HERE / "cyborg_kernel.py").read_text(encoding="utf-8")
    # v1.1 may import subprocess only inside lattice_net for git/hf
    net_src = (ck.KERNEL / "lattice_net.py").read_text(encoding="utf-8")
    has_net = "urllib.request" in net_src
    ok = (
        boot.get("ready")
        and d.get("ok")
        and out.get("can_claim_done")
        and pulse.get("ok") is True
        and has_net
        and ck.VERSION.startswith("1.2")
        and boot.get("limbs", {}).get("lattice_net") is True
    )
    print(
        json.dumps(
            {
                "ok": ok,
                "signature": ck.SIG,
                "version": ck.VERSION,
                "boot_ready": boot.get("ready"),
                "limbs": boot.get("limbs"),
                "continuum_demo": d.get("ok"),
                "task_can_claim_done": out.get("can_claim_done"),
                "lattice_live": pulse.get("live"),
                "lattice_score": pulse.get("score"),
                "star_entries": (pulse.get("star_feed") or {}).get("entry_count"),
                "star_chain_valid": (pulse.get("star_feed") or {}).get("chain_valid"),
                "agora_ready": pulse.get("ready_for_agora"),
                "agora_chart_sha": (pulse.get("agora") or {}).get("chart_sha"),
                "network_limb": has_net,
            },
            indent=2,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
