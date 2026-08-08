#!/usr/bin/env python3
"""Cyborg boot — one command for agents: limbs + map + install order."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cyborg_kernel as ck  # noqa: E402


def main() -> int:
    stack = os.environ.get("LYGO_STACK_ROOT") or None
    if len(sys.argv) > 1 and sys.argv[1] not in ("-h", "--help"):
        stack = sys.argv[1]
    boot = ck.boot_report(stack)
    lat = ck.lattice_map()
    print(
        json.dumps(
            {
                "signature": ck.SIG,
                "boot": boot,
                "lattice": {
                    "install_order": lat.get("install_order"),
                    "plugins": lat.get("openclaw_plugins"),
                    "skillhub": lat.get("skillhub"),
                    "self_police": lat.get("self_police"),
                    "autonomy": lat.get("autonomy"),
                },
                "next_commands": [
                    "python scripts/cyborg_kernel.py demo",
                    "python scripts/cyborg_task.py example > task.json",
                    "python scripts/cyborg_task.py run --task task.json --base .",
                    "openclaw plugins install clawhub:@deepseekoracle/lygo-continuum",
                ],
            },
            indent=2,
        )
    )
    return 0 if boot.get("ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
