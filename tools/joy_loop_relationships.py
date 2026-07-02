"""Joy affinity graph — proximity + interaction history (Phase 3 propagation v2)."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from joy_loop_protocol import JoyLoopEngine, JoyState

ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data" / "joy_loop" / "relationships.json"


class JoyRelationshipGraph:
    def __init__(self) -> None:
        self.affinity: dict[str, dict[str, float]] = {}
        self._load()

    def _load(self) -> None:
        if GRAPH_PATH.is_file():
            try:
                data = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
                self.affinity = data.get("affinity", {})
            except (json.JSONDecodeError, OSError):
                self.affinity = {}

    def save(self) -> None:
        GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
        GRAPH_PATH.write_text(
            json.dumps({"affinity": self.affinity}, indent=2), encoding="utf-8"
        )

    def _pair_key(self, a: str, b: str) -> tuple[str, str]:
        return (a, b) if a < b else (b, a)

    def get_affinity(self, a_id: str, b_id: str) -> float:
        k1, k2 = self._pair_key(a_id, b_id)
        return float(self.affinity.get(k1, {}).get(k2, 0.0))

    def record_propagation(self, a_id: str, b_id: str, transfer: float) -> None:
        k1, k2 = self._pair_key(a_id, b_id)
        self.affinity.setdefault(k1, {})
        cur = self.affinity[k1].get(k2, 0.0)
        self.affinity[k1][k2] = min(1.0, cur + abs(transfer) * 2.5)

    def apply_affinity_boost(self, engine: "JoyLoopEngine", radius: float) -> None:
        """Propagation with affinity-weighted transfer (v2)."""
        with engine._lock:
            states = list(engine.states.values())
            if len(states) < 2:
                return
            for i, sa in enumerate(states):
                for sb in states[i + 1 :]:
                    x1, y1, z1 = sa.lattice_coordinates
                    x2, y2, z2 = sb.lattice_coordinates
                    dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2)
                    if dist >= radius:
                        continue
                    boost = self.get_affinity(sa.champion_id, sb.champion_id)
                    transfer = (sa.joy_coherence - sb.joy_coherence) * (0.08 + boost * 0.06)
                    sa.joy_coherence = max(0.0, min(1.0, sa.joy_coherence - transfer * 0.6))
                    sb.joy_coherence = max(0.0, min(1.0, sb.joy_coherence + transfer * 0.6))
                    self.record_propagation(sa.champion_id, sb.champion_id, transfer)

    def to_plotly_edges(self) -> list[dict[str, Any]]:
        edges = []
        for a, neighbors in self.affinity.items():
            for b, w in neighbors.items():
                if w > 0.05:
                    edges.append({"source": a, "target": b, "weight": round(w, 3)})
        return edges

    def summary(self) -> dict[str, Any]:
        return {"edge_count": len(self.to_plotly_edges()), "affinity": self.affinity}