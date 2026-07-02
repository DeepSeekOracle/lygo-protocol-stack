"""LYGO Phase 7 — Human-AI Interface Platform (HAIP)."""

from __future__ import annotations

__version__ = "Δ9Φ963-PHASE7-v1.0"

from .data_pipeline import BiometricPipeline
from .device_abstraction import (
    AppleWatchAdapter,
    BiometricReading,
    CustomSensorAdapter,
    DeviceAdapter,
    GarminAdapter,
    OuraAdapter,
    create_adapter,
)
from .ethical_mapping import EthicalVectorMapper
from .entropy_extraction import BiometricEntropyHarness, extract_p0_seed_from_ibi

__all__ = [
    "BiometricPipeline",
    "BiometricReading",
    "DeviceAdapter",
    "AppleWatchAdapter",
    "GarminAdapter",
    "OuraAdapter",
    "CustomSensorAdapter",
    "create_adapter",
    "EthicalVectorMapper",
    "BiometricEntropyHarness",
    "extract_p0_seed_from_ibi",
    "__version__",
]