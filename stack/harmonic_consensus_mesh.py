"""Harmonic consensus mesh — 3/6/9 vortex voting weighted by ethical mass."""

from __future__ import annotations

import math
import time
import uuid
from typing import Any


class HarmonicConsensusEngine:
    def __init__(self) -> None:
        self.harmonic_map = {
            3: 0.0,
            6: 2.0 * math.pi / 3.0,
            9: 4.0 * math.pi / 3.0,
            -1: math.pi,
        }

    def compute_harmonic_center(self, votes: list[dict[str, Any]]) -> tuple[int, float]:
        if not votes:
            return -1, 0.0
        total_weight = 0.0
        ax = 0.0
        ay = 0.0
        for record in votes:
            vote_val = int(record.get("vote", -1))
            weight = float(record.get("ethical_mass", 1.0))
            if vote_val not in self.harmonic_map:
                continue
            angle = self.harmonic_map[vote_val]
            ax += weight * math.cos(angle)
            ay += weight * math.sin(angle)
            total_weight += weight
        if total_weight == 0.0:
            return -1, 0.0
        mx, my = ax / total_weight, ay / total_weight
        harmony_score = math.sqrt(mx * mx + my * my)
        result_angle = math.atan2(my, mx)
        if result_angle < 0:
            result_angle += 2.0 * math.pi
        closest = -1
        min_delta = float("inf")
        for gate, target_angle in self.harmonic_map.items():
            delta = min(abs(result_angle - target_angle), 2.0 * math.pi - abs(result_angle - target_angle))
            if delta < min_delta:
                min_delta = delta
                closest = gate
        if closest == -1:
            # π-axis tie between 6↔9 (or mixed 3/6/9): fall back to ethical-mass-weighted 9>6>3.
            tally: dict[int, float] = {3: 0.0, 6: 0.0, 9: 0.0}
            for record in votes:
                vote_val = int(record.get("vote", -1))
                if vote_val in tally:
                    tally[vote_val] += float(record.get("ethical_mass", 1.0))
            if any(tally.values()):
                closest = max(tally.items(), key=lambda kv: (kv[1], kv[0]))[0]
        return closest, round(harmony_score, 4)


class ProposalManager:
    def __init__(self, engine: HarmonicConsensusEngine | None = None, vote_window_sec: float = 60.0) -> None:
        self.engine = engine or HarmonicConsensusEngine()
        self.vote_window_sec = vote_window_sec
        self.proposals: dict[str, dict[str, Any]] = {}
        self.votes: dict[str, list[dict[str, Any]]] = {}
        self.results: dict[str, dict[str, Any]] = {}

    def propose(self, author: str, title: str, description: str = "") -> dict[str, Any]:
        pid = f"PROP_{uuid.uuid4().hex[:8]}"
        prop = {
            "proposal_id": pid,
            "author": author,
            "title": title,
            "description": description,
            "timestamp": time.time(),
            "status": "PENDING",
            "signature": "Δ9Φ963-SLM-v1.0",
        }
        self.proposals[pid] = prop
        self.votes[pid] = []
        return prop

    def vote(self, proposal_id: str, node_id: str, vote: int, ethical_mass: float) -> dict[str, Any]:
        if proposal_id not in self.proposals:
            return {"ok": False, "error": "unknown proposal"}
        if vote not in (3, 6, 9, -1):
            return {"ok": False, "error": "vote must be 3, 6, 9, or -1"}
        entry = {
            "proposal_id": proposal_id,
            "node_id": node_id,
            "vote": vote,
            "ethical_mass": ethical_mass,
            "timestamp": time.time(),
        }
        self.votes[proposal_id] = [v for v in self.votes[proposal_id] if v["node_id"] != node_id]
        self.votes[proposal_id].append(entry)
        return {"ok": True, "vote": entry}

    def finalize(self, proposal_id: str) -> dict[str, Any]:
        if proposal_id not in self.proposals:
            return {"ok": False, "error": "unknown proposal"}
        vote_list = self.votes.get(proposal_id) or []
        decision, harmony_score = self.engine.compute_harmonic_center(vote_list)
        result = {
            "proposal_id": proposal_id,
            "decision": decision,
            "harmony_score": harmony_score,
            "participants": len(vote_list),
            "timestamp": time.time(),
            "status": "FINALIZED" if decision in (3, 6, 9) else "DISSONANT",
            "signature": "Δ9Φ963-SLM-v1.0",
        }
        self.results[proposal_id] = result
        self.proposals[proposal_id]["status"] = result["status"]
        return result

    def get_result(self, proposal_id: str) -> dict[str, Any] | None:
        if proposal_id in self.results:
            return self.results[proposal_id]
        prop = self.proposals.get(proposal_id)
        if not prop:
            return None
        age = time.time() - float(prop.get("timestamp", 0))
        if age >= self.vote_window_sec and self.votes.get(proposal_id):
            return self.finalize(proposal_id)
        return {"proposal_id": proposal_id, "status": prop["status"], "votes": len(self.votes.get(proposal_id) or [])}