"""Deterministic synthetic CSI — the falsifier for P10.

Real ESP32 hardware is the point of this protocol; the generator exists so the
physics core, the quantiser and the anchor chain can be tested against a
*known* breathing rate, motion profile and noise level with no sensor present.

Determinism is explicit: a local LCG (not ``random``) drives every draw, so the
same seed yields byte-identical frames on any interpreter.
"""

from __future__ import annotations

import math
from typing import Sequence

from .csi_core import CSIFrame, DEFAULT_SUBCARRIERS

_MASK = 0xFFFFFFFF


class _LCG:
    """Numerical Recipes LCG — reproducible everywhere, no stdlib dependency."""

    def __init__(self, seed: int) -> None:
        self.state = (seed ^ 0x9E3779B9) & _MASK or 1

    def next_u32(self) -> int:
        self.state = (1664525 * self.state + 1013904223) & _MASK
        return self.state

    def uniform(self) -> float:
        """Uniform in [-1, 1)."""
        return (self.next_u32() / 0x80000000) - 1.0

    def gauss(self) -> float:
        """Irwin-Hall(4) approximation — bounded tails, deterministic, cheap."""
        s = self.uniform() + self.uniform() + self.uniform() + self.uniform()
        return s * 0.5


def synthesize_csi(
    duration_s: float = 30.0,
    fs_hz: float = 100.0,
    breathing_bpm: float = 0.0,
    motion_windows: Sequence[tuple[float, float]] = (),
    seed: int = 963,
    subcarriers: int = DEFAULT_SUBCARRIERS,
    rssi: int = -48,
    noise: float = 1.0,
    breathing_gain: float = 4.0,
    motion_gain: float = 6.0,
    start_t_us: int = 0,
    room_profile: int = 0,
) -> list[CSIFrame]:
    """Emit CSI frames for a room.

    Parameters
    ----------
    breathing_bpm
        0 disables the chest signal. Otherwise the *common mode* of every
        subcarrier is modulated at this rate, which is what a real chest
        displacement does (a path-length change, not a per-subcarrier event).
    motion_windows
        ``(start_s, end_s)`` pairs where a person is walking — broadband
        coherent energy well above the empty-room floor.
    noise
        Independent per-subcarrier receiver noise (in amplitude units).
    room_profile
        Shifts the static per-subcarrier channel shape — a *different room*, not
        a different person. ``0`` is the reference room used by the golden
        vectors; do not change 0 without regenerating them.
    """
    lcg = _LCG(seed)
    n = int(duration_s * fs_hz)
    step_us = int(1e6 / fs_hz)

    base_amp = [12.0 + 6.0 * math.sin(0.7 * i + 0.5 * room_profile) for i in range(subcarriers)]
    base_phase = [0.5 * math.sin(1.3 * i) for i in range(subcarriers)]
    breath_hz = breathing_bpm / 60.0

    frames: list[CSIFrame] = []
    for idx in range(n):
        t_s = idx / fs_hz
        common = 0.0
        if breathing_bpm > 0.0:
            common += breathing_gain * math.sin(2.0 * math.pi * breath_hz * t_s)
        moving = any(lo <= t_s < hi for lo, hi in motion_windows)
        if moving:
            common += motion_gain * lcg.gauss()

        amps: list[float] = []
        phases: list[float] = []
        for i in range(subcarriers):
            # Subcarrier weight: a reflection shifts every subcarrier, but not
            # by an identical amount (per-subcarrier phase response).
            weight = 0.6 + 0.4 * math.cos(0.9 * i)
            amps.append(max(0.5, base_amp[i] + weight * common + noise * lcg.gauss()))
            phases.append(base_phase[i] + 0.02 * weight * common + 0.05 * noise * lcg.gauss())
        frames.append(
            CSIFrame(
                seq=idx,
                t_us=start_t_us + idx * step_us,
                rssi=rssi + int(round(lcg.uniform() * 2.0)),
                amplitudes=tuple(amps),
                phases=tuple(phases),
            )
        )
    return frames
