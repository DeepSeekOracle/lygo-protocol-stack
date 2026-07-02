#!/usr/bin/env python3
"""Phase 6 polish — hardened attestation verification with ethical gate."""

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


def fetch_badge(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--peer", default="http://127.0.0.1:8787", help="Node base URL")
    ap.add_argument("--local", action="store_true", help="Verify locally generated badge")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    from protocol6_quantum_attest.attestation import AttestationService
    from protocol6_quantum_attest.measurement import MeasurementCollector
    from lygo_stack import deploy_stack

    if args.local:
        badge = deploy_stack("HARDENED_VERIFY").get_hardware_badge()
        source = "local_stack"
    else:
        try:
            badge = fetch_badge(args.peer.rstrip("/") + "/attestation/badge")
            source = args.peer
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            out = {"status": "FAIL", "reason": str(exc), "source": args.peer}
            print(json.dumps(out, indent=2))
            return 1

    att = AttestationService(MeasurementCollector(), node_id=str(badge.get("node_id", "VERIFY")))
    result = att.verify_badge_detailed(badge)
    report = {"source": source, **result, "status": "PASS" if result["valid"] else "FAIL"}

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("\n" + "=" * 70)
        print("HARDENED ATTESTATION VERIFICATION")
        print("=" * 70)
        for k in ("valid", "alignment", "ethical_gate", "p0_match", "signature_valid", "fresh"):
            if k in result:
                mark = "OK" if result[k] else "FAIL"
                print(f"  {k}: {mark}")
        if result.get("reasons"):
            print("  reasons:")
            for r in result["reasons"]:
                print(f"    - {r}")
        print("=" * 70)

    return 0 if result.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())