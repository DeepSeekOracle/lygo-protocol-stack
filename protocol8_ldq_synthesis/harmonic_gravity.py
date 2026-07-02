"""Seed-driven harmonic parameters (BPM, root frequency) for LDQ synthesis."""

from __future__ import annotations

import math


class HarmonicGravity:
    """Maps a numeric seed to musical parameters using golden-ratio bands."""

    PHI = (1.0 + math.sqrt(5.0)) / 2.0

    def __init__(self, seed_int: int) -> None:
        self.seed_int = int(seed_int) & 0xFFFFFFFFFFFFFFFF

    def get_all_parameters(self) -> dict[str, float]:
        s = self.seed_int
        bpm = 72.0 + (s % 48) + (s >> 8) % 12
        root = 110.0 * (self.PHI ** ((s % 7) - 3))
        root = max(55.0, min(880.0, root))
        intensity = 0.35 + ((s >> 16) % 1000) / 1000.0 * 0.55
        return {
            "bpm": float(bpm),
            "root_frequency": float(root),
            "intensity": float(intensity),
            "phi_band": float(self.PHI),
        }