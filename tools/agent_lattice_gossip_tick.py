#!/usr/bin/env python3
"""
Epidemic agent-directory gossip tick: push local card + pull remote directory; merge.

Summaries only — agent presence cards, never memory/tools payloads.
"""
from __future__ import annotations

import argparse
import json
import random
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
    ap.add_argument("--fanout", type=int, default=3)
    ap.add_argument("--agent-id", default="")
    ap.add_argument("--role", default="agent")
    ap.add_argument("--allow-unaligned", action="store_true")
    args = ap.parse_args()

    card = build_agent_card(
        agent_id=args.agent_id or None,
        role=args.role,
        require_aligned=not args.allow_unaligned,
    )
    errs = validate_card(card, require_aligned=not args.allow_unaligned)
    if errs and "quarantine_card" in errs:
        print(json.dumps({"verdict": "BLOCKED", "errors": errs}))
        return 3

    directory = AgentDirectory()
    directory.upsert(card, source="local")

    peers = list(args.peer or [])
    if not peers:
        peers = [p.get("base_url") for p in load_peers() if p.get("base_url")]
    random.shuffle(peers)
    targets = peers[: max(1, args.fanout)] if peers else []

    pushes, pulls, merges = [], [], []
    for base in targets:
        # push announce
        st, resp = http_json(
            "POST",
            base.rstrip("/") + "/agent/announce",
            {"card": card, "signature": SIG, "from": card["agent_id"]},
        )
        pushes.append({"peer": base, "http": st, "ok": 200 <= int(st) < 300})

        # pull directory
        st2, resp2 = http_json("GET", base.rstrip("/") + "/agent/directory")
        pulls.append({"peer": base, "http": st2, "ok": 200 <= int(st2) < 300})
        if isinstance(resp2, dict):
            agents = resp2.get("agents") or []
            if isinstance(agents, dict):
                agents = list(agents.values())
            for item in agents:
                c = item.get("card") if isinstance(item, dict) and "card" in item else item
                if not isinstance(c, dict):
                    continue
                r = directory.upsert(c, source=f"gossip:{base}")
                merges.append({"agent_id": c.get("agent_id"), "ok": r.get("ok"), "errors": r.get("errors")})

        # optional scatter of our snapshot digests
        snap = directory.snapshot()
        summary = {
            "signature": SIG,
            "from": card["agent_id"],
            "directory_digest": snap.get("directory_digest"),
            "agent_count": snap.get("agent_count"),
            "cards": snap.get("agents") or [],
        }
        st3, _ = http_json("POST", base.rstrip("/") + "/agent/gossip", summary)
        pushes.append({"peer": base, "path": "/agent/gossip", "http": st3, "ok": 200 <= int(st3) < 300})

    report = {
        "signature": SIG,
        "timestamp": utc_now(),
        "local_agent_id": card["agent_id"],
        "local_digest": card.get("digest"),
        "directory_digest": directory.snapshot().get("directory_digest"),
        "agent_count": len(directory.list_cards()),
        "pushes": pushes,
        "pulls": pulls,
        "merges": merges[:50],
        "verdict": "GOSSIP_OK"
        if (not targets) or any(p.get("ok") for p in pushes)
        else "GOSSIP_SOFT_FAIL",
    }
    if not targets:
        report["verdict"] = "LOCAL_DIRECTORY_OK"
        report["note"] = "no peers — local directory updated only"

    out = ROOT / "tests" / "agent_lattice_gossip_last_run.json"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass
    print(json.dumps(report, indent=2))
    return 0 if report["verdict"] in ("GOSSIP_OK", "LOCAL_DIRECTORY_OK") else 1


if __name__ == "__main__":
    raise SystemExit(main())
