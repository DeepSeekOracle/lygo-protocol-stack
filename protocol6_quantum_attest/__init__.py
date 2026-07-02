"""LYGO Protocol 6 — Hardware Attestation (Δ9Φ963-PHASE6-v1.0)."""

from __future__ import annotations

__version__ = "Δ9Φ963-PHASE6-v1.0"

from .attestation import AttestationService
from .measurement import MeasurementCollector, get_p0_hash
from .tpm_interface import check_tpm
from .puf_arbiter import check_puf

__all__ = [
    "AttestationService",
    "MeasurementCollector",
    "get_p0_hash",
    "check_tpm",
    "check_puf",
    "__version__",
]