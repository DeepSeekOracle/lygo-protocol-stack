#!/usr/bin/env python3
"""
Hierarchical manifest builder + P6 provenance.

Canonical: tools/scalable_registry/manifest_builder.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scalable_registry.manifest_builder import (  # noqa: F401
    MAX_MANIFEST_JSON_BYTES,
    anchor_manifest_local,
    anchor_manifest_tree,
    build_manifest,
    build_manifest_from_bytes,
    build_manifest_from_file,
    build_manifest_from_hashes,
    expand_chunk_hashes,
    manifest_content_sha256,
)
from scalable_registry.registry_manager import CAS_ROOT, add_manifest_entry, persist_manifest

ROOT = Path(__file__).resolve().parents[1]


def build_manifest_and_register(
    file_path: str | Path,
    metadata: dict[str, Any],
    node_id: str,
    *,
    require_p6: bool = True,
    anchor: bool = False,
) -> dict[str, Any]:
    """Full lattice path: build → persist → append registry."""
    manifest = build_manifest(
        file_path,
        metadata,
        node_id,
        require_p6=require_p6,
        anchor=anchor,
    )
    manifest["content_sha256"] = manifest_content_sha256(manifest)
    persist_manifest(manifest)
    global_root = add_manifest_entry(
        str(manifest["manifest_id"]),
        str(manifest["merkle_root"]),
        content_sha256=manifest["content_sha256"],
        metadata=metadata,
    )
    return {"manifest": manifest, "global_merkle_root": global_root}