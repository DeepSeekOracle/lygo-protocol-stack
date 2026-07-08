#!/usr/bin/env python3
"""Shim — harmonic consensus engine (see stack/harmonic_consensus_mesh.py)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stack"))

from harmonic_consensus_mesh import HarmonicConsensusEngine, ProposalManager  # noqa: E402

__all__ = ["HarmonicConsensusEngine", "ProposalManager"]

if __name__ == "__main__":
    print("[*] TEST: Harmonic Consensus Engine")
    engine = HarmonicConsensusEngine()
    votes = [
        {"node_id": "n1", "vote": 9, "ethical_mass": 1.618},
        {"node_id": "n2", "vote": 9, "ethical_mass": 1.25},
        {"node_id": "n3", "vote": 6, "ethical_mass": 0.85},
        {"node_id": "n4", "vote": 3, "ethical_mass": 0.9},
        {"node_id": "n5", "vote": -1, "ethical_mass": 0.31},
    ]
    decision, score = engine.compute_harmonic_center(votes)
    print(f"[>] decision={decision} harmony={score}")
    raise SystemExit(0 if decision in (3, 6, 9) else 1)