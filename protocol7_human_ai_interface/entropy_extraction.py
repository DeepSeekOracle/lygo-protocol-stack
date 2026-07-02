"""IBI → min-entropy estimate → von Neumann debias → LHL (HMAC) P0 seed."""

from __future__ import annotations

import hashlib
import hmac
import math
from collections import Counter
from typing import Any

P7_SIGNATURE = "Δ9Φ963-PHASE7-v1.0"
DEFAULT_SALT = b"LYGO-P7-LHL-SALT-v1"


def high_pass_detrend(ibi_ms: list[float], alpha: float = 0.9) -> list[float]:
    if not ibi_ms:
        return []
    out: list[float] = []
    prev = ibi_ms[0]
    for x in ibi_ms:
        prev = alpha * (prev + x - (out[-1] if out else x)) + (1 - alpha) * x
        out.append(x - prev)
    return out


def von_neumann_extract(bits: list[int]) -> list[int]:
    """Pairwise unbiased bit extraction."""
    unbiased: list[int] = []
    i = 0
    while i + 1 < len(bits):
        a, b = bits[i], bits[i + 1]
        if a != b:
            unbiased.append(0 if (a, b) == (0, 1) else 1)
        i += 2
    return unbiased


def ibi_to_bits(ibi_ms: list[float], bins: int = 16) -> list[int]:
    if not ibi_ms:
        return []
    lo, hi = min(ibi_ms), max(ibi_ms)
    span = hi - lo or 1.0
    bits: list[int] = []
    for v in ibi_ms:
        bucket = int((v - lo) / span * (bins - 1))
        for b in range(4):
            bits.append((bucket >> b) & 1)
    return bits


def estimate_min_entropy(ibi_ms: list[float], bins: int = 8) -> float:
    if len(ibi_ms) < 2:
        return 0.0
    lo, hi = min(ibi_ms), max(ibi_ms)
    span = hi - lo or 1.0
    counts = Counter(int((v - lo) / span * (bins - 1)) for v in ibi_ms)
    n = sum(counts.values())
    p_max = max(counts.values()) / n
    return max(0.0, -math.log2(p_max))


def extract_p0_seed_from_ibi(
    ibi_ms: list[float],
    *,
    salt: bytes = DEFAULT_SALT,
    min_entropy_bits: float = 1.0,
) -> dict[str, Any]:
    detrended = high_pass_detrend(ibi_ms)
    h_min = estimate_min_entropy(detrended or ibi_ms)
    bits = von_neumann_extract(ibi_to_bits(detrended or ibi_ms))
    payload = ",".join(f"{x:.3f}" for x in (detrended or ibi_ms))
    seed = hmac.new(salt, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    sufficient = h_min >= min_entropy_bits and len(bits) >= 4
    return {
        "signature": P7_SIGNATURE,
        "h_min": round(h_min, 4),
        "von_neumann_bits": len(bits),
        "entropy_sufficient": sufficient,
        "seed_256": seed,
        "ibi_count": len(ibi_ms),
    }


class BiometricEntropyHarness:
    """Synthetic + live IBI path into P0 perturbation slot."""

    def __init__(self, min_entropy_bits: float = 1.0):
        self.min_entropy_bits = min_entropy_bits

    def from_biometric_state(self, state: dict[str, Any]) -> dict[str, Any]:
        ibi = state.get("ibi_ms") or []
        if not ibi and state.get("aggregated"):
            hr = state["aggregated"].get("heart_rate") or 70
            ibi = [60000.0 / float(hr)] * 12
        out = extract_p0_seed_from_ibi(ibi, min_entropy_bits=self.min_entropy_bits)
        out["source"] = "biometric_state"
        return out

    def phi_perturbation(self, base_phi: float, seed_hex: str, scale: float = 0.001) -> float:
        h = int(seed_hex[:8], 16)
        unit = (h % 10000) / 10000.0
        return max(0.0, min(1.0, base_phi + (unit - 0.5) * scale))