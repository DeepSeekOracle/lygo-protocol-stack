"""P3 harmonic consensus for multi-agent workflow steps."""

from __future__ import annotations

import math
from typing import Any


class P3VortexConsensus:
    def __init__(self) -> None:
        self.harmonic_map = {
            3: 0.0,
            6: 2.0 * math.pi / 3.0,
            9: 4.0 * math.pi / 3.0,
            -1: math.pi,
        }

    def achieve_consensus(self, data: dict[str, Any], votes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        if votes:
            gate, score = self.compute_harmonic_center(votes)
            return {
                "consensus_found": gate in (3, 6, 9) and score >= 0.5,
                "decision": gate,
                "harmony_score": score,
                "participants": len(votes),
                "governing_number": gate,
            }
        agents = data.get("agents") or data.get("steps") or []
        if isinstance(agents, list) and len(agents) >= 2:
            synthetic = [{"vote": 9, "ethical_mass": 1.0} for _ in range(min(len(agents), 3))]
            gate, score = self.compute_harmonic_center(synthetic)
            return {
                "consensus_found": gate == 9,
                "decision": gate,
                "harmony_score": score,
                "participants": len(synthetic),
                "governing_number": gate,
                "governing_meaning": "COMPLETION — multi-step workflow",
            }
        return {
            "consensus_found": True,
            "decision": 9,
            "harmony_score": 1.0,
            "participants": 1,
            "governing_number": 9,
            "governing_meaning": "COMPLETION — single-agent workflow",
        }

    def compute_harmonic_center(self, votes: list[dict[str, Any]]) -> tuple[int, float]:
        if not votes:
            return -1, 0.0
        total_weight = 0.0
        ax = 0.0
        ay = 0.0
        for record in votes:
            vote_val = record.get("vote", -1)
            weight = float(record.get("ethical_mass", 1.0))
            if vote_val not in self.harmonic_map:
                continue
            angle = self.harmonic_map[vote_val]
            ax += weight * math.cos(angle)
            ay += weight * math.sin(angle)
            total_weight += weight
        if total_weight == 0.0:
            return -1, 0.0
        mean_x = ax / total_weight
        mean_y = ay / total_weight
        harmony_score = math.sqrt(mean_x**2 + mean_y**2)
        result_angle = math.atan2(mean_y, mean_x)
        if result_angle < 0:
            result_angle += 2.0 * math.pi
        closest_gate = -1
        min_delta = float("inf")
        for gate, target_angle in self.harmonic_map.items():
            delta = min(
                abs(result_angle - target_angle),
                2.0 * math.pi - abs(result_angle - target_angle),
            )
            if delta < min_delta:
                min_delta = delta
                closest_gate = gate
        return closest_gate, round(harmony_score, 4)