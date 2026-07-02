#!/usr/bin/env python3
"""LYGO Phase 9 — TPM attestation CLI (Keylime bridge)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from protocol6_quantum_attest.keylime_bridge import KeylimeAttestation  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO Keylime / TPM attestation")
    ap.add_argument("--node-id", default=os.environ.get("LYGO_NODE_ID", "LYGO_NODE"))
    ap.add_argument("--register", action="store_true")
    ap.add_argument("--quote", action="store_true")
    ap.add_argument("--agent-url", default="http://127.0.0.1:9002/v2/")
    args = ap.parse_args()
    kl = KeylimeAttestation(args.node_id, args.agent_url)
    out: dict = {"node_id": args.node_id}
    if args.register:
        out["registered"] = kl.register_node()
    if args.quote or not args.register:
        quote = kl.get_quote()
        out["quote"] = quote
        out["quote_valid"] = KeylimeAttestation.verify_quote(quote)
    print(json.dumps(out, indent=2))
    return 0 if out.get("quote_valid", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())