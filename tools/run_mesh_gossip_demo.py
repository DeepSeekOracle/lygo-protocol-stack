#!/usr/bin/env python3
"""Demo epidemic badge pull against local node API (Phase 5 gossip)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stack"))

from lygo_stack import deploy_stack  # noqa: E402
from mesh_gossip_http import GossipPeer, epidemic_round  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--peer", default="http://127.0.0.1:8787", help="Peer base URL")
    ap.add_argument("--node-id", default="peer-1")
    args = ap.parse_args()

    stack = deploy_stack("MESH_DEMO")
    tools = ROOT / "tools"
    sys.path.insert(0, str(tools))
    from verify_alignment_badge import collect_badge  # noqa: E402

    local = collect_badge(quick=True)
    local["node_id"] = stack.federation.local_node_id
    peers = [GossipPeer(node_id=args.node_id, base_url=args.peer)]
    report = epidemic_round(local, peers, stack.federation)
    print(json.dumps(report, indent=2))
    return 0 if any(p.get("ok") for p in report.get("pulls", [])) or not peers else 1


if __name__ == "__main__":
    raise SystemExit(main())