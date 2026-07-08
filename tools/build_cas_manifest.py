#!/usr/bin/env python3
"""CLI: Biophase7 CAS physics — build manifest, register, verify (lattice wrapper)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from manifest_builder import build_manifest_and_register  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Build CAS manifest from file (stream-safe CDC)")
    ap.add_argument("--file", type=Path, required=True)
    ap.add_argument("--metadata", default="{}")
    ap.add_argument("--node-id", default="LYGO_REGISTRY_NODE")
    ap.add_argument("--no-p6", action="store_true")
    ap.add_argument("--anchor", action="store_true")
    ap.add_argument("--verify", action="store_true", help="Run verify_registry.py after register")
    args = ap.parse_args()

    if not args.file.is_file():
        print(json.dumps({"error": "file not found", "path": str(args.file)}), file=sys.stderr)
        return 1

    metadata = json.loads(args.metadata)
    result = build_manifest_and_register(
        args.file,
        metadata,
        args.node_id,
        require_p6=not args.no_p6,
        anchor=args.anchor,
    )
    print(json.dumps({k: v for k, v in result.items() if k != "manifest"}, indent=2))
    print(
        json.dumps(
            {
                "manifest_id": result["manifest"]["manifest_id"],
                "type": result["manifest"].get("type"),
                "merkle_root": result["manifest"]["merkle_root"],
                "chunk_count": result["manifest"].get("chunk_count"),
            },
            indent=2,
        )
    )

    if args.verify:
        rc = subprocess.call([sys.executable, str(ROOT / "tools" / "verify_registry.py")], cwd=ROOT)
        return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())