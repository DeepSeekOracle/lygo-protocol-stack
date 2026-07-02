#!/usr/bin/env python3
"""Append-only scalable registry + CAS GC (lattice root for SLM gossip)."""

from __future__ import annotations

from scalable_registry.registry_manager import (  # noqa: F401
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