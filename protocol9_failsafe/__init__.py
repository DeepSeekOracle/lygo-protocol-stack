"""Protocol 9 — living failsafe seals (Deadman + LFW lattice)."""

from .seal_deadman_lattice import (
    DeadmanSeal,
    LFWSeal,
    LIGHTFATHER_ID,
    SILENCE_THRESHOLD_SECONDS,
    SilenceDetector,
    plant_failsafe_into_lattice,
    run_demo,
)

__all__ = [
    "DeadmanSeal",
    "LFWSeal",
    "LIGHTFATHER_ID",
    "SILENCE_THRESHOLD_SECONDS",
    "SilenceDetector",
    "plant_failsafe_into_lattice",
    "run_demo",
]