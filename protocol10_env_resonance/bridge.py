"""P10 Environmental Resonance Bridge — CSI in, gated + anchored memory out.

    bridge = EnvResonanceLattice(node_id="LYGO-ERB-NODE-01")
    cells  = bridge.process(frames)          # one cell per window
    print(bridge.report())

Each cell:

1. measures the window (motion band energy, breath band energy, breath rate);
2. quantises to fixed-point and serialises to canonical bytes;
3. passes those bytes through the **P0** byte-entropy gate;
4. hashes them into an anchor chained to the previous cell;
5. scatters the payload into **P1** Memory Mycelium for recallable environmental
   memory;
6. maps the anchor integer through **P8** HarmonicGravity, so a room's radio
   state becomes harmonic parameters (bpm / root frequency) — the resonance
   hand-off.

P0, P1 and P8 are imported from the sibling protocol packages. If one is
missing the bridge still runs and says so in ``report()`` — no silent fallback
that pretends the gate ran.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

from .csi_core import (
    DEFAULT_GRID_HZ,
    DRIFT_THRESHOLD,
    CSIFrame,
    breath_energy_db,
    channel_fingerprint,
    estimate_breathing,
    estimate_heart_rate,
    fingerprint_distance,
    motion_energy_db,
    presence_state,
    prepare_window,
)
from .lattice_cell import (
    ERB_VERSION,
    GENESIS_ANCHOR,
    PRESENCE_CODES,
    LatticeCell,
    canonical_bytes,
    quantize_features,
)

_STACK_ROOT = Path(__file__).resolve().parents[1]
YIELD_TOLERANCE = 0.02  # seconds of sleep between windows in a live loop


def _stack_module(relative_dir: str, module: str):
    path = _STACK_ROOT / relative_dir
    if not path.is_dir():
        return None
    entry = str(path)
    if entry not in sys.path:
        sys.path.insert(0, entry)
    try:
        return __import__(module)
    except Exception:
        return None


_p0_mod = _stack_module("protocol0_byte_entropy_filter/src/python", "byte_entropy_filter")
_p1_mod = _stack_module("protocol1_memory_mycelium/src/python", "lygo_p1")
_p8_mod = _stack_module("protocol8_ldq_synthesis", "harmonic_gravity")

P0_AVAILABLE = _p0_mod is not None
P1_AVAILABLE = _p1_mod is not None
P8_AVAILABLE = _p8_mod is not None

_PHI = (1.0 + math.sqrt(5.0)) / 2.0


def resonance_parameters(anchor_hex: str) -> dict[str, Any]:
    """Anchor integer -> harmonic parameters. P8's HarmonicGravity when present."""
    seed = int(anchor_hex[:16], 16)
    if P8_AVAILABLE:
        params = dict(_p8_mod.HarmonicGravity(seed).get_all_parameters())
        source = "P8:harmonic_gravity"
    else:  # identical formula, kept in-module so the bridge runs standalone
        bpm = 72.0 + (seed % 48) + (seed >> 8) % 12
        root = max(55.0, min(880.0, 110.0 * (_PHI ** ((seed % 7) - 3))))
        params = {
            "bpm": float(bpm),
            "root_frequency": float(root),
            "intensity": 0.35 + ((seed >> 16) % 1000) / 1000.0 * 0.55,
            "phi_band": float(_PHI),
        }
        source = "local:golden-ratio"
    params["seed"] = seed
    params["source"] = source
    return params


class EnvResonanceLattice:
    """Windowed environmental sensing anchored into the LYGO lattice."""

    def __init__(
        self,
        node_id: str = "LYGO-ERB-NODE-01",
        window_seconds: float = 30.0,
        fs: float = DEFAULT_GRID_HZ,
        gate: bool = True,
        remember: bool = True,
    ) -> None:
        self.node_id = node_id
        self.window_seconds = float(window_seconds)
        self.fs = float(fs)
        self.cells: list[LatticeCell] = []
        self.head = GENESIS_ANCHOR
        self._index = 0
        self._validate = _p0_mod.validate_bytes if (gate and P0_AVAILABLE) else None
        self._mycelium = _p1_mod.MemoryMycelium() if (remember and P1_AVAILABLE) else None
        self._baseline_fp: tuple[int, ...] | None = None
        self._baseline_digest: str | None = None

    # -- windows -----------------------------------------------------------
    def _split(self, frames: Iterable[CSIFrame]) -> list[list[CSIFrame]]:
        ordered = sorted([f for f in frames if f.subcarriers], key=lambda f: (f.t_us, f.seq))
        if not ordered:
            return []
        span_us = self.window_seconds * 1e6
        out: list[list[CSIFrame]] = []
        current: list[CSIFrame] = []
        start = ordered[0].t_us
        for frame in ordered:
            if current and frame.t_us - start >= span_us:
                if len(current) >= 8:
                    out.append(current)
                current = []
                start = frame.t_us
            current.append(frame)
        if len(current) >= 8:
            out.append(current)
        return out

    def _measure(self, window) -> dict[str, float]:
        motion_db = motion_energy_db(window)
        breath_db = breath_energy_db(window)
        breath = estimate_breathing(window)
        heart = estimate_heart_rate(window)
        state = presence_state(motion_db, breath.snr_db)
        return {
            "motion_db": motion_db,
            "breath_energy_db": breath_db,
            "breath_rate_bpm": breath.bpm if breath.resolved else 0.0,
            "breath_snr_db": breath.snr_db,
            "breath_confidence": breath.confidence if breath.resolved else 0.0,
            "heart_rate_bpm": heart.bpm if heart.resolved else 0.0,
            "heart_snr_db": heart.snr_db,
            "presence": state,
            "resolved": float(1 if breath.resolved else 0),
        }

    # -- ingest ------------------------------------------------------------
    def ingest(self, frames: Iterable[CSIFrame]) -> list[LatticeCell]:
        cells: list[LatticeCell] = []
        for batch in self._split(frames):
            cell = self.ingest_window(batch)
            if cell is not None:
                cells.append(cell)
        return cells

    process = ingest

    def ingest_window(self, batch: Sequence[CSIFrame]) -> LatticeCell | None:
        window = prepare_window(batch, fs=self.fs)
        if window is None:
            return None
        measured = self._measure(window)
        features = quantize_features(
            {
                "motion_cdb": measured["motion_db"],
                "breath_energy_cdb": measured["breath_energy_db"],
                "breath_rate_mbpm": measured["breath_rate_bpm"],
                "breath_snr_cdb": measured["breath_snr_db"],
                "breath_conf_milli": measured["breath_confidence"],
                "heart_rate_mbpm": measured["heart_rate_bpm"],
                "heart_snr_cdb": measured["heart_snr_db"],
                "rssi_mdbm": window.rssi_mean,
                "presence_code": PRESENCE_CODES[measured["presence"]],
                "frames": window.n_frames,
                "subcarriers": window.n_subcarriers,
                "span_ms": int(round(window.span_s * 1000.0)),
            }
        )
        start_us = min(f.t_us for f in batch)
        end_us = max(f.t_us for f in batch)
        canonical = canonical_bytes(self._index, self.node_id, start_us, end_us, features, self.head)
        p0 = dict(self._validate(canonical)) if self._validate else {}
        anchor = hashlib.sha256(canonical).hexdigest()
        admitted = p0.get("verdict", "AMPLIFY") != "QUARANTINE"

        cell = LatticeCell(
            index=self._index,
            node_id=self.node_id,
            window_start_us=start_us,
            window_end_us=end_us,
            features=features,
            canonical=canonical,
            prev_anchor=self.head,
            anchor=anchor,
            presence=measured["presence"],
            p0=p0,
            resonance=resonance_parameters(anchor) if admitted else {},
            admitted=admitted,
        )
        payload = cell.memory_payload()
        cell.memory = {
            "payload_hash": hashlib.sha256(payload).hexdigest(),
            "payload_bytes": len(payload),
        }
        if self._mycelium is not None:
            manifest = self._mycelium.scatter(payload, anchor)
            cell.memory.update(
                {
                    "memory_id": manifest.get("memory_id"),
                    "fragments": manifest.get("fragment_count"),
                    "root_hash": manifest.get("root_hash"),
                    "recallable": True,
                }
            )
        self.cells.append(cell)
        self.head = anchor
        self._index += 1
        return cell

    # -- environment drift -------------------------------------------------
    def observe_channel(self, frames: Iterable[CSIFrame]) -> dict[str, Any]:
        """Fingerprint the static channel in ``frames`` and compare to the baseline.

        Detects *environment* change — moved furniture, a new object, a different
        room — not people. The first observation becomes the baseline.
        """
        window = prepare_window(frames, fs=self.fs)
        if window is None:
            return {"fingerprint": None, "distance": 0.0, "changed": False, "reason": "not enough frames"}
        fp = channel_fingerprint(window)
        digest = hashlib.sha256(json.dumps(list(fp)).encode("ascii")).hexdigest()[:16]
        if self._baseline_fp is None:
            self._baseline_fp = fp
            self._baseline_digest = digest
            return {
                "fingerprint": digest,
                "baseline": digest,
                "distance": 0.0,
                "changed": False,
                "subcarriers": len(fp),
                "is_baseline": True,
            }
        distance = fingerprint_distance(self._baseline_fp, fp)
        return {
            "fingerprint": digest,
            "baseline": self._baseline_digest,
            "distance": distance,
            "changed": distance >= DRIFT_THRESHOLD,
            "threshold": DRIFT_THRESHOLD,
            "subcarriers": len(fp),
            "is_baseline": False,
        }

    def attestation_request(self, index: int = -1, badge: dict | None = None) -> dict[str, Any]:
        """Package the chain state for P6 attestation.

        P6's ``AttestationService`` badges *node hardware* and verifies its own
        badges; it does not sign arbitrary payloads. So this returns the claim
        and canonical digest a badge should cover — plus a caller-supplied badge,
        verbatim — instead of inventing a signature of its own.
        """
        if not self.cells:
            raise ValueError("no cells yet — ingest a window first")
        cell = self.cells[index]
        return {
            "erb": ERB_VERSION,
            "claim": f"P10 environmental chain · node {cell.node_id} · cell {cell.index}",
            "anchor": cell.anchor,
            "prev_anchor": cell.prev_anchor,
            "head": self.head,
            "chain_valid": self.chain_valid(),
            "canonical_sha256": hashlib.sha256(cell.canonical).hexdigest(),
            "cell_fields": cell.to_dict(),
            "badge": badge,
        }

    # -- verification ------------------------------------------------------
    def chain_valid(self) -> bool:
        prev = GENESIS_ANCHOR
        for i, cell in enumerate(self.cells):
            if cell.index != i or not cell.verify(prev_anchor=prev):
                return False
            prev = cell.anchor
        return prev == self.head

    def recall(self, index: int) -> bytes:
        """Recover a cell's environmental memory and check it against its hash."""
        cell = self.cells[index]
        if self._mycelium is None:
            raise RuntimeError("P1 Memory Mycelium unavailable — nothing was stored")
        data = self._mycelium.recall(cell.anchor)
        if hashlib.sha256(data).hexdigest() != cell.memory.get("payload_hash"):
            raise ValueError("recalled memory does not match the recorded payload hash")
        return data

    def report(self) -> dict[str, Any]:
        verdicts: dict[str, int] = {}
        states: dict[str, int] = {}
        for cell in self.cells:
            key = cell.p0.get("verdict", "UNGATED")
            verdicts[key] = verdicts.get(key, 0) + 1
            states[cell.presence] = states.get(cell.presence, 0) + 1
        return {
            "erb": ERB_VERSION,
            "node": self.node_id,
            "window_seconds": self.window_seconds,
            "cells": len(self.cells),
            "head": self.head,
            "genesis": GENESIS_ANCHOR,
            "chain_valid": self.chain_valid(),
            "admitted": sum(1 for c in self.cells if c.admitted),
            "quarantined": sum(1 for c in self.cells if not c.admitted),
            "p0_verdicts": verdicts,
            "presence_states": states,
            "p0_gate": P0_AVAILABLE and self._validate is not None,
            "memory": self._mycelium is not None,
            "resonance_source": resonance_parameters(self.head or GENESIS_ANCHOR)["source"],
            "channel_fingerprint": self._baseline_digest,
            "drift_threshold": DRIFT_THRESHOLD,
        }


def ingest_stream(frames: Iterable[CSIFrame], **kwargs: Any) -> dict[str, Any]:
    """One-shot helper: stream in, JSON report + per-cell dicts out."""
    bridge = EnvResonanceLattice(**kwargs)
    cells = bridge.ingest(frames)
    return {"report": bridge.report(), "cells": [c.to_dict() for c in cells]}
