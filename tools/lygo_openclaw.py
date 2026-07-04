#!/usr/bin/env python3
"""CLI — LYGO-OpenClaw sovereign agent framework."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lygo_openclaw import LYGOOpenClaw  # noqa: E402
from lygo_openclaw.memory import P1MemoryMycelium  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO-OpenClaw")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Run gated limb command")
    p_run.add_argument("command")
    p_run.add_argument("args", nargs="*", default=[])
    p_run.add_argument("--config")
    p_run.add_argument("--no-anchor", action="store_true")

    p_rec = sub.add_parser("recall", help="Recall mycelium memory_id")
    p_rec.add_argument("memory_id")

    p_val = sub.add_parser("validate", help="P0 validate command string")
    p_val.add_argument("text")

    args = ap.parse_args()

    if args.cmd == "run":
        cfg = Path(args.config) if args.config else None
        out = LYGOOpenClaw(config_path=cfg).run(
            args.command, list(args.args), skip_anchor=args.no_anchor
        )
        print(json.dumps(out, indent=2))
        return 0 if out.get("ok") else 2

    if args.cmd == "recall":
        data = P1MemoryMycelium().recall(args.memory_id)
        if data is None:
            print("not found", file=sys.stderr)
            return 1
        print(json.dumps(data, indent=2))
        return 0

    if args.cmd == "validate":
        from lygo_openclaw.gatekeeper import P0Gatekeeper  # noqa: E402

        print(json.dumps(P0Gatekeeper().validate(args.text), indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())