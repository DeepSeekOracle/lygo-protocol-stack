#!/usr/bin/env python3
"""
Append-only scalable registry + CAS garbage collection.

Blueprint match: tools/registry_manager.py
- load_registry / save_registry / add_manifest_entry
- prune_cas(max_gb) with LYGO_MAX_LOCAL_CAS_GB (default 50)
- CLI: status, list, prune, add-entry (advanced)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from scalable_registry.registry_manager import (  # noqa: E402
    CAS_ROOT,
    MANIFESTS_DIR,
    REGISTRY_FILE,
    add_manifest_entry,
    cas_total_bytes,
    collect_protected_chunk_hashes,
    default_max_cas_gb,
    ensure_dirs,
    load_manifest,
    load_registry,
    persist_manifest,
    prune_cas,
    recompute_global_root,
    save_registry,
)

SIGNATURE = "Δ9Φ963-REGISTRY-MANAGER-v2"


def registry_status() -> dict[str, Any]:
    ensure_dirs()
    reg = load_registry()
    return {
        "signature": SIGNATURE,
        "registry_file": str(REGISTRY_FILE),
        "global_merkle_root": reg.get("global_merkle_root"),
        "entry_count": len(reg.get("entries") or []),
        "cas_bytes": cas_total_bytes(),
        "cas_root": str(CAS_ROOT),
        "default_max_cas_gb": default_max_cas_gb(),
    }


def list_entries() -> list[dict[str, Any]]:
    reg = load_registry()
    return list(reg.get("entries") or [])


def repair_orphan_manifest_files() -> dict[str, Any]:
    """Remove on-disk manifests that fail expand (e.g. after CAS prune)."""
    from scalable_registry.manifest_builder import expand_chunk_hashes

    reg = load_registry()
    active_ids = {str(e.get("id")) for e in reg.get("entries") or []}
    removed: list[str] = []
    kept_entries = []
    for e in reg.get("entries") or []:
        m = load_manifest(str(e.get("id") or ""))
        if not m:
            continue
        try:
            expand_chunk_hashes(m)
            kept_entries.append(e)
        except Exception:
            pass
    for mf in list(MANIFESTS_DIR.glob("*.json")):
        try:
            data = json.loads(mf.read_text(encoding="utf-8"))
            expand_chunk_hashes(data)
        except Exception:
            mf.unlink(missing_ok=True)
            removed.append(mf.name)
    reg["entries"] = kept_entries
    reg["global_merkle_root"] = recompute_global_root(kept_entries)
    save_registry(reg)
    return {"removed_files": removed, "entries": len(kept_entries)}


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO scalable registry manager")
    ap.add_argument("--status", action="store_true", help="JSON status (default)")
    ap.add_argument("--list", action="store_true", help="List registry entries")
    ap.add_argument("--prune-cas-gb", type=float, default=None, help="Prune CAS to max GB")
    ap.add_argument("--repair", action="store_true", help="Drop broken manifest files / entries")
    ap.add_argument(
        "--add-entry",
        nargs=3,
        metavar=("MANIFEST_ID", "MERKLE_ROOT", "CONTENT_SHA256"),
        help="Append registry entry (maintainer)",
    )
    args = ap.parse_args()

    if args.repair:
        print(json.dumps(repair_orphan_manifest_files(), indent=2))

    if args.prune_cas_gb is not None:
        stats = prune_cas(args.prune_cas_gb, protect_hashes=collect_protected_chunk_hashes())
        print(json.dumps({"prune_cas": stats}, indent=2))

    if args.add_entry:
        mid, root, sha = args.add_entry
        g = add_manifest_entry(mid, root, content_sha256=sha, metadata={"manual": True})
        print(json.dumps({"global_merkle_root": g, "manifest_id": mid}, indent=2))

    if args.list:
        for e in list_entries():
            print(
                e.get("id"),
                (e.get("merkle_root") or "")[:16],
                (e.get("metadata") or {}).get("name", ""),
            )
        return 0

    if args.status or not any(
        [args.prune_cas_gb is not None, args.repair, args.add_entry, args.list]
    ):
        print(json.dumps(registry_status(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())