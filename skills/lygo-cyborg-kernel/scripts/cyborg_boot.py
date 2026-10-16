#!/usr/bin/env python3
"""Cyborg boot — limbs + optional live lattice connect."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SKILL / "kernel"))
import cyborg_kernel as ck  # noqa: E402
import lattice_net as net  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stack_root", nargs="?", default=None)
    ap.add_argument("--connect", action="store_true", help="Also pulse lattice + git connect")
    ap.add_argument("--hf", action="store_true")
    args = ap.parse_args()
    stack = args.stack_root or os.environ.get("LYGO_STACK_ROOT")
    boot = ck.boot_report(stack)
    lat = ck.lattice_map()
    live = None
    if args.connect:
        live = net.auto_connect(stack, use_git=True, use_hf=args.hf)
        if live.get("stack_root"):
            boot = ck.boot_report(live["stack_root"])
    print(
        json.dumps(
            {
                "signature": ck.SIG,
                "version": ck.VERSION,
                "boot": boot,
                "lattice_map": {
                    "install_order": lat.get("install_order"),
                    "plugins": lat.get("openclaw_plugins"),
                    "skillhub": lat.get("skillhub"),
                    "network": lat.get("network"),
                },
                "live_connect": live,
                "next": [
                    "python scripts/cyborg_connect.py",
                    "python scripts/cyborg_star.py status",
                    "python scripts/cyborg_talk.py",
                    "python scripts/cyborg_talk.py say status",
                ],
            },
            indent=2,
            default=str,
        )
    )
    ok = boot.get("ready")
    if args.connect:
        ok = bool(ok and live and live.get("ok"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
