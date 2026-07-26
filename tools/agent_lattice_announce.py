#!/usr/bin/env python3
"""
Announce local agent card to peers (alignment-gated).

Consent not required for local directory upsert; peer announce is operator intent.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from agent_lattice_core import (  # noqa: E402
    AgentDirectory,
    SIG,
    build_agent_card,
    http_json,
    load_peers,
    utc_now,
    validate_card,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--peer", action="append", default=[])
    ap.add_argument("--agent-id", default="")
    ap.add_argument("--role", default="agent")
    ap.add_argument("--endpoint", default="")
    ap.add_argument("--require-aligned", action="store_true", default=True)
    ap.add_argument("--allow-unaligned", action="store_true")
    ap.add_argument("--ttl", type=int, default=1800)
    args = ap.parse_args()

    card = build_agent_card(
        agent_id=args.agent_id or None,
        role=args.role,
        endpoint=args.endpoint,
        ttl_sec=args.ttl,
        require_aligned=not args.allow_unaligned,
    )
    require = not args.allow_unaligned
    errs = validate_card(card, require_aligned=require)
    if errs:
        print(json.dumps({"verdict": "BLOCKED", "errors": errs, "card_id": card.get("agent_id")}))
        return 3 if "quarantine_card" in errs else 2

    directory = AgentDirectory()
    local = directory.upsert(card, source="local")

    peers = list(args.peer or [])
    if not peers:
        peers = [p.get("base_url") for p in load_peers() if p.get("base_url")]

    results = []
    for base in peers:
        url = base.rstrip("/") + "/agent/announce"
        status, resp = http_json("POST", url, {"card": card, "signature": SIG, "from": card["agent_id"]})
        results.append(
            {
                "peer": base,
                "http": status,
                "ok": 200 <= int(status) < 300,
                "resp": resp if isinstance(resp, dict) else str(resp)[:240],
            }
        )

    report = {
        "signature": SIG,
        "timestamp": utc_now(),
        "agent_id": card["agent_id"],
        "digest": card.get("digest"),
        "alignment_status": card.get("alignment_status"),
        "local_upsert": local,
        "pushes": results,
        "verdict": "ANNOUNCED"
        if local.get("ok") and (not peers or any(r.get("ok") for r in results))
        else ("LOCAL_ONLY" if local.get("ok") else "FAILED"),
    }
    out = ROOT / "tests" / "agent_lattice_announce_last_run.json"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass
    print(json.dumps(report, indent=2))
    return 0 if report["verdict"] in ("ANNOUNCED", "LOCAL_ONLY") else 1


if __name__ == "__main__":
    raise SystemExit(main())
