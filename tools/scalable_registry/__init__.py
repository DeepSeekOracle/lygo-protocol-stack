"""Scalable Kernel Egg Registry — CDC, CAS, hierarchical manifests, SLM roots."""

from __future__ import annotations

SIGNATURE = "Δ9Φ963-SCALABLE-REGISTRY-v2"
MAX_MANIFEST_JSON_BYTES = 85_000  # v2: under 100 KiB Turbo (85 KiB split threshold)
SUB_MANIFEST_MAX_HASHES = 1_000  # v2 directive: ≤1000 hashes per sub-manifest
DEFAULT_MAX_LOCAL_CAS_GB = 50.0
CAS_SUBDIR_DEPTH = 2  # data/cas/ab/cd/<fullhash>