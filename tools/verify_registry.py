#!/usr/bin/env python3
"""Verify scalable registry integrity + P6 provenance."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from scalable_registry.registry_manager import prune_cas, collect_protected_chunk_hashes  # noqa: E402
from scalable_registry.verify import run_full_verify  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--prune-cas-gb", type=float, default=None)
    args = ap.parse_args()

    if args.prune_cas_gb is not None:
        stats = prune_cas(args.prune_cas_gb, protect_hashes=collect_protected_chunk_hashes())
        print(json.dumps({"prune_cas": stats}, indent=2))

    report = run_full_verify(write_artifact=True)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"verdict={report['verdict']} all_pass={report['all_pass']}")
        print(f"global_merkle_root={report.get('global_merkle_root', '')[:32]}…")
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())