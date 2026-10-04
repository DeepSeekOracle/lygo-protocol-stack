"""P10 lattice cell — fixed-point quantisation, canonical bytes, SHA-256 anchor.

The determinism contract: *the same CSI window produces the same anchor*. The
mechanism is that nothing floating-point ever reaches the hash. Every measured
quantity is quantised onto a fixed integer grid first, so last-bit differences
in ``sin``/``log10`` cannot move the anchor except on a razor-edge tie.

Anchor chain: ``anchor_n = SHA256(canonical_bytes_n || anchor_{n-1})``. Cells
carry the anchor of their predecessor, so a dropped, reordered or edited cell
is detectable from the head alone — the same tamper-evidence property P1 uses
for memory fragments.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping

ERB_VERSION = "P10.1.0-ERB"
GENESIS_ANCHOR = "0" * 64

# name -> integer scale. centi-dB, milli-BPM, milli-unit, plain counts.
FEATURE_SCALE: dict[str, int] = {
    "motion_cdb": 100,
    "breath_energy_cdb": 100,
    "breath_rate_mbpm": 1000,
    "breath_snr_cdb": 100,
    "breath_conf_milli": 1000,
    "heart_rate_mbpm": 1000,
    "heart_snr_cdb": 100,
    "rssi_mdbm": 1000,
    "presence_code": 1,
    "frames": 1,
    "subcarriers": 1,
    "span_ms": 1,
}

FEATURE_ORDER: tuple[str, ...] = tuple(sorted(FEATURE_SCALE))

PRESENCE_CODES = {"CLEAR": 0, "SUBTLE": 1, "ACTIVE": 2, "PRESENT": 3}


def quantize_features(features: Mapping[str, float | int]) -> dict[str, int]:
    """Snap measured values onto the fixed integer grid (round-half-away-from-zero)."""
    missing = [name for name in FEATURE_ORDER if name not in features]
    if missing:
        raise ValueError(f"missing features: {missing}")
    out: dict[str, int] = {}
    for name in FEATURE_ORDER:
        scale = FEATURE_SCALE[name]
        value = features[name]
        scaled = float(value) * scale
        out[name] = int(scaled + 0.5) if scaled >= 0 else -int(-scaled + 0.5)
    return out


def canonical_bytes(
    index: int,
    node_id: str,
    window_start_us: int,
    window_end_us: int,
    features: Mapping[str, int],
    prev_anchor: str,
) -> bytes:
    """Canonical, integer-only serialisation — the exact bytes that get hashed."""
    unknown = [name for name in features if name not in FEATURE_SCALE]
    if unknown:
        raise ValueError(f"unknown features: {unknown}")
    payload = {
        "erb": ERB_VERSION,
        "node": node_id,
        "index": int(index),
        "t0_us": int(window_start_us),
        "t1_us": int(window_end_us),
        "prev": prev_anchor,
        "features": {name: int(features[name]) for name in FEATURE_ORDER if name in features},
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


@dataclass
class LatticeCell:
    """One anchored window of environmental state."""

    index: int
    node_id: str
    window_start_us: int
    window_end_us: int
    features: dict[str, int]
    canonical: bytes
    prev_anchor: str
    anchor: str
    presence: str = "CLEAR"
    p0: dict[str, Any] = field(default_factory=dict)
    resonance: dict[str, float] = field(default_factory=dict)
    memory: dict[str, Any] = field(default_factory=dict)
    admitted: bool = True

    @property
    def span_ms(self) -> int:
        return (self.window_end_us - self.window_start_us) // 1000

    def verify(self, prev_anchor: str | None = None) -> bool:
        """Recompute the anchor and re-read every field out of the hashed bytes.

        Hashing alone is not enough: an editor can leave ``canonical`` and
        ``anchor`` untouched and rewrite ``features`` — the readable
        interpretation. So the canonical payload is decoded and compared
        field-by-field against the cell.
        """
        if hashlib.sha256(self.canonical).hexdigest() != self.anchor:
            return False
        try:
            payload = json.loads(self.canonical.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return False
        if payload.get("index") != self.index or payload.get("node") != self.node_id:
            return False
        if payload.get("t0_us") != self.window_start_us or payload.get("t1_us") != self.window_end_us:
            return False
        if payload.get("prev") != self.prev_anchor:
            return False
        if payload.get("features") != {k: int(v) for k, v in self.features.items()}:
            return False
        if prev_anchor is not None and self.prev_anchor != prev_anchor:
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "node": self.node_id,
            "window_us": [self.window_start_us, self.window_end_us],
            "span_ms": self.span_ms,
            "presence": self.presence,
            "admitted": self.admitted,
            "anchor": self.anchor,
            "prev_anchor": self.prev_anchor,
            "p0_verdict": self.p0.get("verdict"),
            "p0_score": self.p0.get("score"),
            "features": dict(self.features),
            "resonance": dict(self.resonance),
            "memory_root": self.memory.get("root_hash"),
        }

    def memory_payload(self) -> bytes:
        """Bytes handed to P1 Memory Mycelium (self-describing, hash-friendly).

        Strings (the resonance ``source``) stay strings; numbers are rounded to
        a fixed precision so the payload hash is stable.
        """
        resonance = {
            k: (v if isinstance(v, str) else round(float(v), 6))
            for k, v in self.resonance.items()
        }
        body = {
            "erb": ERB_VERSION,
            "node": self.node_id,
            "index": self.index,
            "anchor": self.anchor,
            "prev": self.prev_anchor,
            "presence": self.presence,
            "admitted": self.admitted,
            "features": dict(self.features),
            "resonance": resonance,
        }
        return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
