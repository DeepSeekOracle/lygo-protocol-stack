#!/usr/bin/env python3
"""CLI for LYGO Sovereign Workflow Orchestrator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lygo_sandcastle import LYGOWorkflowOrchestrator  # noqa: E402
from lygo_sandcastle.memory import P1MemoryMycelium  # noqa: E402


def cmd_run(args: argparse.Namespace) -> int:
    path = Path(args.workflow)
    if not path.is_file():
        print(f"missing workflow: {path}", file=sys.stderr)
        return 1
    orch = LYGOWorkflowOrchestrator(
        config_path=Path(args.config) if args.config else None,
    )
    out = orch.run(path.read_text(encoding="utf-8"), skip_anchor=args.no_anchor)
    print(json.dumps(out, indent=2))
    return 0 if out.get("ok") or "error" not in out else 2


def cmd_recall(args: argparse.Namespace) -> int:
    mem = P1MemoryMycelium()
    data = mem.recall(args.memory_id)
    if data is None:
        print("not found", file=sys.stderr)
        return 1
    print(json.dumps(data, indent=2))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    from lygo_sandcastle.gatekeeper import P0Gatekeeper  # noqa: E402

    path = Path(args.workflow)
    g = P0Gatekeeper()
    print(json.dumps(g.validate(path.read_text(encoding="utf-8")), indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO Sovereign Workflow Orchestrator")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Run workflow YAML")
    p_run.add_argument("workflow")
    p_run.add_argument("--config")
    p_run.add_argument("--no-anchor", action="store_true")
    p_run.set_defaults(func=cmd_run)

    p_rec = sub.add_parser("recall", help="Recall mycelium memory_id")
    p_rec.add_argument("memory_id")
    p_rec.set_defaults(func=cmd_recall)

    p_val = sub.add_parser("validate", help="P0-validate workflow YAML only")
    p_val.add_argument("workflow")
    p_val.set_defaults(func=cmd_validate)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())