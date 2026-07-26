#!/usr/bin/env python3
"""Consent-gated join to agent lattice peer hub."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from agent_lattice_core import (  # noqa: E402
    SIG,
    build_agent_card,
    http_json,
    save_peer,
    validate_card,
)


def consent(flag: bool) -> bool:
    if flag:
        return True
    return os.environ.get("LYGO_AGENT_LATTICE_JOIN_CONSENT", "").lower() in ("1", "yes", "true")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--i-consent", action="store_true")
    ap.add_argument("--peer", required=True, help="Hub base URL e.g. http://127.0.0.1:8787")
    ap.add_argument("--label", default="")
    ap.add_argument("--agent-id", default="")
    ap.add_argument("--role", default="agent")
    ap.add_argument("--allow-unaligned", action="store_true")
    args = ap.parse_args()

    if not consent(args.i_consent):
        print(json.dumps({"verdict": "BLOCKED", "reason": "consent_required"}))
        return 2

    card = build_agent_card(
        agent_id=args.agent_id or None,
        role=args.role,
        require_aligned=not args.allow_unaligned,
    )
    errs = validate_card(card, require_aligned=not args.allow_unaligned)
    if errs:
        print(json.dumps({"verdict": "BLOCKED", "errors": errs, "protection": "refuse_join"}))
        return 3

    entry = save_peer(args.peer, args.label)
    # announce immediately
    st, resp = http_json(
        "POST",
        args.peer.rstrip("/") + "/agent/announce",
        {"card": card, "signature": SIG, "from": card["agent_id"]},
    )
    print(
        json.dumps(
            {
                "verdict": "JOINED",
                "peer": entry,
                "announce_http": st,
                "announce_ok": 200 <= int(st) < 300,
                "announce_resp": resp if isinstance(resp, dict) else str(resp)[:200],
                "agent_id": card["agent_id"],
                "digest": card.get("digest"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
