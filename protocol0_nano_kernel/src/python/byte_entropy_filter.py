"""
Byte-entropy anomaly filter — honest name for P0.4 canonical behavior.

Canonical verdicts and golden SHA-256 remain on lygo_p0.validate_bytes (stride compression).
This module re-exports the canonical API and adds zlib diagnostics for calibration only.
"""

from __future__ import annotations

import zlib
from typing import Any

from lygo_p0 import (
    COMP_MIN_LEN,
    ENTROPY_HIGH,
    ENTROPY_LOW,
    MAX_BYTES,
    PHI_MAX,
    PHI_MIN,
    canonical_line,
    compression_ratio,
    entropy_norm,
    load_vectors,
    run_vector_suite,
    validate_bytes,
)

__all__ = [
    "MAX_BYTES",
    "ENTROPY_LOW",
    "ENTROPY_HIGH",
    "PHI_MIN",
    "PHI_MAX",
    "COMP_MIN_LEN",
    "validate_bytes",
    "entropy_norm",
    "compression_ratio",
    "zlib_compression_ratio",
    "canonical_line",
    "load_vectors",
    "run_vector_suite",
]


def zlib_compression_ratio(data: bytes) -> float:
    """Real zlib ratio in [0,1]; higher = more compressible. Not used for canonical verdicts."""
    if len(data) < COMP_MIN_LEN:
        return 0.0
    try:
        compressed = zlib.compress(data, level=6)
        ratio = 1.0 - (len(compressed) / len(data))
        return max(0.0, min(1.0, ratio))
    except Exception:
        return 0.0


def diagnose(data: bytes) -> dict[str, Any]:
    """Side-by-side canonical vs zlib metrics (no verdict change)."""
    res = validate_bytes(data)
    res["zlib_compression"] = round(zlib_compression_ratio(data), 4)
    return res