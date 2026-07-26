#!/usr/bin/env python3
"""
Consent-gated mesh join: record peer pin, require local ALIGNED, optional first gossip.

Does not open public ports by itself — use node_api_server for that.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from collect_living_mesh_badge import collect_living_badge  # noqa: E402

SIG = "Delta9Phi963-LIVING-MESH-JOIN-v1"
PEERS = ROOT / "data" / "living_mesh" / "peers.json"


def consent(flag: bool) -> bool:
    if flag:
        return True
    return os.environ.get("LYGO_MESH_JOIN_CONSENT", "").lower() in ("1", "yes", "true")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--i-consent", action="store_true")
    ap.add_argument("--peer", required=True, help="Peer base URL http(s)://host:port")
    ap.add_argument("--label", default="")
    ap.add_argument("--require-aligned", action="store_true", default=True)
    args = ap.parse_args()
    if not consent(args.i_consent):
        print(json.dumps({"verdict": "BLOCKED", "reason": "consent_required"}))
        return 2

    badge = collect_living_badge(quick=True)
    status = (badge.get("living_mesh") or {}).get("local_status")
    if args.require_aligned and status == "QUARANTINE":
        print(json.dumps({"verdict": "BLOCKED", "reason": "local_QUARANTINE", "protection": "refuse_join"}))
        return 3

    peers = {"signature": SIG, "peers": []}
    if PEERS.is_file():
        peers = json.loads(PEERS.read_text(encoding="utf-8"))
    entry = {
        "base_url": args.peer.rstrip("/"),
        "label": args.label or args.peer,
        "joined_utc": datetime.now(timezone.utc).isoformat(),
        "local_node_id": badge.get("node_id"),
        "local_roots_digest": (badge.get("living_mesh") or {}).get("roots_digest"),
    }
    # dedupe
    peers["peers"] = [p for p in peers.get("peers") or [] if p.get("base_url") != entry["base_url"]]
    peers["peers"].append(entry)
    peers["updated_utc"] = entry["joined_utc"]
    PEERS.parent.mkdir(parents=True, exist_ok=True)
    PEERS.write_text(json.dumps(peers, indent=2) + "\n", encoding="utf-8")

    # first tick optional
    import subprocess

    subprocess.run(
        [sys.executable, str(ROOT / "tools" / "living_mesh_gossip_tick.py"), "--peer", entry["base_url"]],
        cwd=str(ROOT),
    )
    print(json.dumps({"verdict": "JOINED", "peer": entry, "peers_file": str(PEERS)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
