"""LDQ friction — Φ-risk wave shaping (clip + soft fold)."""

from __future__ import annotations

import numpy as np


class FrictionCore:
    def __init__(self, phi_risk: float = 0.618) -> None:
        self.phi_risk = float(max(0.1, min(1.618, phi_risk)))

    def process(self, signal: np.ndarray) -> np.ndarray:
        x = np.asarray(signal, dtype=np.float64)
        drive = 1.0 + self.phi_risk
        y = np.tanh(x * drive)
        threshold = 0.85 - (self.phi_risk * 0.25)
        y = np.clip(y, -threshold, threshold)
        # mild wavefold on peaks
        mask = np.abs(y) > threshold * 0.92
        if np.any(mask):
            y[mask] = np.sign(y[mask]) * (threshold - (np.abs(y[mask]) - threshold) * 0.35)
        return y