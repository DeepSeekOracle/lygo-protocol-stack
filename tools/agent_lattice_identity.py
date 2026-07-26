#!/usr/bin/env python3
"""Build / show local LYGO agent lattice identity card."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from agent_lattice_core import (  # noqa: E402
    LOCAL_FILE,
    build_agent_card,
    validate_card,
    _save,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent-id", default="")
    ap.add_argument("--role", default="agent")
    ap.add_argument("--display-name", default="")
    ap.add_argument("--endpoint", default="")
    ap.add_argument("--skill", action="append", default=[])
    ap.add_argument("--cap", action="append", default=[])
    ap.add_argument("--ttl", type=int, default=1800)
    ap.add_argument("--out", default="")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    card = build_agent_card(
        agent_id=args.agent_id or None,
        role=args.role,
        display_name=args.display_name,
        endpoint=args.endpoint,
        skills=args.skill or None,
        capabilities=args.cap or None,
        ttl_sec=args.ttl,
    )
    errs = validate_card(card)
    _save(LOCAL_FILE, {"card": card, "validated": not errs, "errors": errs})
    if args.out:
        Path(args.out).write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"card": card, "errors": errs, "local_file": str(LOCAL_FILE)}, indent=2))
    return 3 if "quarantine_card" in errs or "secret_pattern" in errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
