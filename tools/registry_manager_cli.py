#!/usr/bin/env python3
"""Registry admin: show root, prune CAS, export status."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from scalable_registry.registry_manager import (  # noqa: E402
    cas_total_bytes,
    collect_protected_chunk_hashes,
    load_registry,
    prune_cas,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--prune-cas-gb", type=float, default=None)
    args = ap.parse_args()

    if args.prune_cas_gb is not None:
        stats = prune_cas(args.prune_cas_gb, protect_hashes=collect_protected_chunk_hashes())
        print(json.dumps(stats, indent=2))

    if args.status or args.prune_cas_gb is None:
        reg = load_registry()
        print(
            json.dumps(
                {
                    "global_merkle_root": reg.get("global_merkle_root"),
                    "entries": len(reg.get("entries") or []),
                    "cas_bytes": cas_total_bytes(),
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())