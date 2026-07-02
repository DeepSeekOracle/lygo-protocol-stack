#!/usr/bin/env python3
"""Register synthetic data / weights: CDC → CAS → hierarchical manifest → append-only registry."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from scalable_registry.manifest_builder import (  # noqa: E402
    anchor_manifest_local,
    build_manifest_from_bytes,
    build_manifest_from_file,
    manifest_content_sha256,
)
from scalable_registry.registry_manager import (  # noqa: E402
    CAS_ROOT,
    add_manifest_entry,
    collect_protected_chunk_hashes,
    persist_manifest,
    prune_cas,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO Scalable Registry — register dataset")
    ap.add_argument("--file", type=Path, help="Input file (streamed; safe for large files)")
    ap.add_argument("--metadata", default="{}", help="JSON metadata")
    ap.add_argument("--node-id", default="LYGO_REGISTRY_NODE")
    ap.add_argument("--no-p6", action="store_true", help="Skip P6 signature (dev/test only)")
    ap.add_argument("--anchor", action="store_true", help="Anchor manifest via lygo_anchor")
    ap.add_argument("--prune-cas-gb", type=float, default=None, help="Run prune_cas after register")
    args = ap.parse_args()

    metadata = json.loads(args.metadata)
    require_p6 = not args.no_p6

    if args.file:
        if not args.file.is_file():
            print(f"Missing file: {args.file}", file=sys.stderr)
            return 1
        manifest = build_manifest_from_file(
            args.file,
            metadata,
            CAS_ROOT,
            node_id=args.node_id,
            require_p6=require_p6,
        )
    else:
        data = sys.stdin.buffer.read()
        manifest = build_manifest_from_bytes(
            data,
            metadata,
            CAS_ROOT,
            node_id=args.node_id,
            require_p6=require_p6,
        )

    mid = str(manifest["manifest_id"])
    manifest["content_sha256"] = manifest_content_sha256(manifest)
    persist_manifest(manifest)

    anchor_info = None
    if args.anchor:
        anchor_info = anchor_manifest_local(manifest)

    global_root = add_manifest_entry(
        mid,
        str(manifest["merkle_root"]),
        content_sha256=manifest["content_sha256"],
        metadata=metadata,
        anchor=anchor_info,
    )

    if args.prune_cas_gb is not None:
        protected = collect_protected_chunk_hashes()
        stats = prune_cas(args.prune_cas_gb, protect_hashes=protected)
        print(json.dumps({"prune_cas": stats}, indent=2))

    print(
        json.dumps(
            {
                "manifest_id": mid,
                "merkle_root": manifest["merkle_root"],
                "type": manifest.get("type"),
                "global_merkle_root": global_root,
                "chunk_count": manifest.get("chunk_count"),
                "anchored": bool(anchor_info),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())