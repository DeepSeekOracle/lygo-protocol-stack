"""Scalable Kernel Egg Registry — CDC, CAS, hierarchical manifests, SLM roots."""

from __future__ import annotations

SIGNATURE = "Δ9Φ963-SCALABLE-REGISTRY-v1"
MAX_MANIFEST_JSON_BYTES = 90_000  # engineering override: stay under 100 KiB Turbo
CAS_SUBDIR_DEPTH = 2  # data/cas/ab/cd/<fullhash>