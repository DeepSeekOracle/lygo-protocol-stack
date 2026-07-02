"""Protocol 8 — LDQ live synthesis (harmonic gravity + friction + sequencer)."""

from .friction_core_engine import FrictionCore
from .harmonic_gravity import HarmonicGravity
from .lyra_sequencer import LYRASequencer

P8_VERSION = "Δ9Φ963-PHASE9-LDQ-v1.0"

__all__ = ["HarmonicGravity", "FrictionCore", "LYRASequencer", "P8_VERSION"]