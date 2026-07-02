#!/usr/bin/env python3
"""Fetch and verify a peer hardware attestation badge."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "stack"))


def fetch_badge(peer_base: str) -> dict:
    url = peer_base.rstrip("/") + "/attestation/badge"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--peer", required=True, help="Peer base URL e.g. http://127.0.0.1:8787")
    ap.add_argument("--badge-file", help="Verify local JSON file instead of HTTP fetch")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    from lygo_stack import deploy_stack  # noqa: E402

    stack = deploy_stack("PEER_VERIFY")
    if args.badge_file:
        badge = json.loads(Path(args.badge_file).read_text(encoding="utf-8"))
        source = args.badge_file
    else:
        try:
            badge = fetch_badge(args.peer)
            source = args.peer
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            out = {"valid": False, "error": str(exc), "peer": args.peer}
            print(json.dumps(out, indent=2))
            return 1

    valid = stack.verify_peer_badge(badge)
    out = {
        "valid": valid,
        "source": source,
        "node_id": badge.get("node_id"),
        "signature": "Δ9Φ963-PHASE6-v1.0",
    }
    print(json.dumps(out, indent=2))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())