#!/usr/bin/env python3
"""
Verify scalable registry: global Merkle root, P6 provenance, CAS integrity.

Blueprint match: tools/verify_registry.py
- Rejects tampered manifests (QUARANTINE)
- Writes tests/scalable_registry_last_run.json for lattice /badge
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from scalable_registry.manifest_builder import expand_chunk_hashes  # noqa: E402
from scalable_registry.registry_manager import load_manifest, load_registry  # noqa: E402
from scalable_registry.verify import (  # noqa: E402
    run_full_verify,
    verify_manifest_file,
    verify_registry_entries,
)

SIGNATURE = "Δ9Φ963-VERIFY-REGISTRY-v2"


def verify_one_manifest(manifest_id: str, *, strict: bool = False) -> dict:
    m = load_manifest(manifest_id)
    if m is None:
        return {"manifest_id": manifest_id, "pass": False, "note": "not found"}
    if strict:
        prov = m.get("provenance") or {}
        if prov.get("note") == "unsigned_dev" or not prov.get("merkle_root_signature"):
            return {"manifest_id": manifest_id, "pass": False, "note": "unsigned (strict)"}
    ok, note = verify_manifest_file(m)
    if ok:
        try:
            expand_chunk_hashes(m)
        except Exception as exc:
            ok, note = False, str(exc)
    return {"manifest_id": manifest_id, "pass": ok, "note": note}


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify LYGO scalable registry")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="Reject unsigned dev manifests")
    ap.add_argument("--manifest-id", default=None, help="Verify single manifest")
    ap.add_argument("--repair", action="store_true", help="Run registry_manager --repair first")
    ap.add_argument("--prune-cas-gb", type=float, default=None)
    args = ap.parse_args()

    if args.repair:
        import subprocess

        subprocess.call(
            [sys.executable, str(ROOT / "tools" / "registry_manager.py"), "--repair"],
            cwd=ROOT,
        )

    if args.prune_cas_gb is not None:
        from scalable_registry.registry_manager import collect_protected_chunk_hashes, prune_cas

        print(json.dumps({"prune_cas": prune_cas(args.prune_cas_gb, protect_hashes=collect_protected_chunk_hashes())}, indent=2))

    if args.manifest_id:
        one = verify_one_manifest(args.manifest_id, strict=args.strict)
        print(json.dumps(one, indent=2))
        return 0 if one["pass"] else 1

    ok_root, msg_root = verify_registry_entries()
    report = run_full_verify(write_artifact=True)
    if args.strict:
        for c in report.get("checks", []):
            if "unsigned" in str(c.get("note", "")):
                c["pass"] = False
        report["all_pass"] = all(c.get("pass") for c in report.get("checks", []))
        report["verdict"] = "ALIGNED" if report["all_pass"] else "QUARANTINE"

    report["signature"] = SIGNATURE
    report["root_check"] = {"pass": ok_root, "note": msg_root}

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"verdict={report['verdict']} all_pass={report['all_pass']}")
        print(f"global_merkle_root={str(report.get('global_merkle_root', ''))[:32]}…")
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())