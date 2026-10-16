#!/usr/bin/env python3
"""
Cyborg connect — join live LYGO lattice via HTTPS, git, optional Hugging Face.

  python scripts/cyborg_connect.py
  python scripts/cyborg_connect.py --dest D:\\lygo-protocol-stack
  python scripts/cyborg_connect.py --hf
  python scripts/cyborg_connect.py --pulse-only

Signature: Delta9Phi963-CYBORG-KERNEL-v1.2.0
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(SKILL / "kernel"))
import lattice_net as net  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO Cyborg lattice connect (git/HF/HTTPS)")
    ap.add_argument("--dest", default=None, help="Stack clone path / LYGO_STACK_ROOT")
    ap.add_argument("--hf", action="store_true", help="Also pull Hugging Face dataset snapshot")
    ap.add_argument("--no-git", action="store_true", help="Skip git clone/pull")
    ap.add_argument("--pulse-only", action="store_true", help="HTTPS lattice pulse only")
    ap.add_argument("--agora-only", action="store_true", help="Agent Agora snapshot only")
    ap.add_argument("--timeout", type=float, default=25.0)
    args = ap.parse_args()

    if args.pulse_only:
        out = net.lattice_pulse(timeout=args.timeout)
    elif args.agora_only:
        out = net.agora_snapshot(timeout=args.timeout)
    else:
        out = net.auto_connect(
            args.dest,
            use_git=not args.no_git,
            use_hf=args.hf,
            timeout=args.timeout,
        )
    print(json.dumps(out, indent=2, default=str))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
