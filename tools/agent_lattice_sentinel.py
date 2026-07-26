#!/usr/bin/env python3
"""Agent lattice sentinel — local card health + directory + optional peer pull."""
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
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--allow-unaligned", action="store_true")
    args = ap.parse_args()

    card = build_agent_card(require_aligned=not args.allow_unaligned)
    errs = validate_card(card, require_aligned=not args.allow_unaligned)
    directory = AgentDirectory()
    directory.upsert(card, source="sentinel") if not errs else None
    snap = directory.snapshot()

    peers = list(args.peer or []) + [p.get("base_url") for p in load_peers() if p.get("base_url")]
    peers = list(dict.fromkeys([p for p in peers if p]))
    peer_health = []
    for base in peers:
        st, resp = http_json("GET", base.rstrip("/") + "/agent/directory")
        peer_health.append(
            {
                "peer": base,
                "http": st,
                "ok": 200 <= int(st) < 300,
                "remote_count": (resp or {}).get("agent_count") if isinstance(resp, dict) else None,
                "remote_digest": (resp or {}).get("directory_digest") if isinstance(resp, dict) else None,
            }
        )

    verdict = "SENTINEL_OK"
    if "quarantine_card" in errs or card.get("alignment_status") == "QUARANTINE":
        verdict = "SENTINEL_QUARANTINE"
    elif errs and not args.allow_unaligned:
        verdict = "SENTINEL_BLOCKED"
    elif peer_health and not any(p.get("ok") for p in peer_health):
        verdict = "SENTINEL_PEERS_DOWN"

    report = {
        "signature": SIG,
        "timestamp": utc_now(),
        "local_agent_id": card.get("agent_id"),
        "alignment_status": card.get("alignment_status"),
        "card_errors": errs,
        "directory_digest": snap.get("directory_digest"),
        "agent_count": snap.get("agent_count"),
        "peers": peer_health,
        "verdict": verdict,
    }
    out = ROOT / "tests" / "agent_lattice_sentinel_last_run.json"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass
    print(json.dumps(report, indent=2))
    return 3 if verdict == "SENTINEL_QUARANTINE" else (1 if verdict == "SENTINEL_BLOCKED" else 0)


if __name__ == "__main__":
    raise SystemExit(main())
