"""
LYGO Protocol 3 — Vortex Consensus (P3.0)
Tesla 3-6-9 harmonic consensus with SHA-256 vortex reduction and Φ filtering.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from typing import Any, Dict, List, Tuple

__version__ = "P3.0"

PHI = 1.618033988749895
PHI_MIN = 0.618
PHI_MAX = 1.618
TESLA_TRINITY = (3, 6, 9)

# Hexagonal lattice coordinates for vortex digits 1-9
HEX_POSITIONS: Dict[int, Tuple[int, int]] = {
    1: (0, 0),
    2: (1, 0),
    3: (2, 0),
    4: (0, 1),
    5: (1, 1),
    6: (2, 1),
    7: (0, 2),
    8: (1, 2),
    9: (2, 2),
}


class VortexConsensusSync:
    """Harmonic multi-node consensus engine."""

    def __init__(self, kernel: Any, mycelium: Any, sovereign_id: str):
        self.kernel = kernel
        self.mycelium = mycelium
        self.sovereign_id = sovereign_id
        self.consensus_history: List[Dict] = []
        self.vortex_cycle = 0

    @property
    def node_id(self) -> str:
        return self.sovereign_id

    def vortex_digit_from_data(self, data: str) -> int:
        """Reduce SHA-256 digest to vortex digit 1-9."""
        digest = hashlib.sha256(data.encode("utf-8")).digest()
        total = sum(digest)
        digit = total % 9
        return 9 if digit == 0 else digit

    def vortex_signature(self, data: str) -> Dict:
        digit = self.vortex_digit_from_data(data)
        hx, hy = HEX_POSITIONS.get(digit, (1, 1))
        governing = self._governing_number(digit)
        return {
            "vortex_digit": digit,
            "hex_coord": (hx, hy),
            "governing": governing,
            "sha256_prefix": hashlib.sha256(data.encode("utf-8")).hexdigest()[:16],
        }

    def _governing_number(self, digit: int) -> str:
        if digit in (3, 6, 9):
            if digit == 3:
                return "Creation"
            if digit == 6:
                return "Relation"
            return "Completion"
        # Map non-trinity to nearest harmonic category
        if digit in (1, 2, 4):
            return "Creation"
        if digit in (5, 7):
            return "Relation"
        return "Completion"

    def _hex_distance(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    def _harmony_score(self, q_sig: Dict, r_sig: Dict) -> float:
        d_q, d_r = q_sig["vortex_digit"], r_sig["vortex_digit"]
        digit_score = 1.0 - min(abs(d_q - d_r) / 9.0, 1.0)
        hex_score = 1.0 - min(self._hex_distance(q_sig["hex_coord"], r_sig["hex_coord"]) / 3.0, 1.0)
        gov_bonus = 0.1 if q_sig["governing"] == r_sig["governing"] else 0.0
        raw = 0.5 * digit_score + 0.4 * hex_score + gov_bonus
        return PHI_MIN + raw * (PHI_MAX - PHI_MIN)

    def achieve_consensus(self, question: str, responses: List[Dict]) -> Dict:
        """Filter Φ-aligned responses and select harmonic center."""
        if not responses:
            return {"error": "No responses", "consensus_found": False}

        q_sig = self.vortex_signature(question)
        weighted: List[Dict] = []

        for resp in responses:
            text = str(resp.get("response", ""))
            r_sig = self.vortex_signature(text)
            harmony = self._harmony_score(q_sig, r_sig)
            if PHI_MIN <= harmony <= PHI_MAX:
                weighted.append(
                    {
                        "response": text,
                        "node_id": resp.get("node_id", "unknown"),
                        "weight": float(resp.get("weight", 1.0)),
                        "harmony": round(harmony, 4),
                        "signature": r_sig,
                    }
                )

        if not weighted:
            return {
                "error": "No Φ-aligned responses",
                "consensus_found": False,
                "harmony_score": 0.0,
                "question_signature": q_sig,
            }

        weighted.sort(key=lambda x: (abs(x["harmony"] - PHI), -x["weight"]))
        optimal = weighted[0]
        kernel_check = self.kernel.validate(optimal["response"])

        record = {
            "question": question,
            "consensus": optimal["response"],
            "harmonic_center": optimal["response"],
            "optimal_node": optimal["node_id"],
            "harmony_score": optimal["harmony"],
            "vortex_alignment": optimal["harmony"],
            "governing": optimal["signature"]["governing"],
            "question_signature": q_sig,
            "response_signature": optimal["signature"],
            "kernel_validation": kernel_check,
            "participants": len(weighted),
            "total_responses": len(responses),
            "filtered_out": len(responses) - len(weighted),
            "consensus_found": True,
            "vortex_cycle": self.vortex_cycle,
            "timestamp": time.time(),
        }

        key = f"VORTEX_CONSENSUS_{self.vortex_cycle}"
        self.mycelium.scatter(record, key)
        self.consensus_history.append(record)
        self.vortex_cycle += 1
        return record


if __name__ == "__main__":
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    for p in (
        root / "protocol0_byte_entropy_filter/src/python",
        root / "protocol1_memory_mycelium/src/python",
        root / "stack",
    ):
        sys.path.insert(0, str(p))
    from kernel_bridge import NanoKernelBridge  # noqa: E402
    from lygo_p1 import MemoryMycelium  # noqa: E402

    print("🌀 LYGO P3 Vortex Consensus — test harness")
    v = VortexConsensusSync(NanoKernelBridge(), MemoryMycelium(), "P3_TEST")
    responses = [
        {"node_id": "A", "response": "Prioritize open verification and Φ-gated releases"},
        {"node_id": "B", "response": "Harmonize documentation with deterministic test vectors"},
        {"node_id": "C", "response": "Maximize throughput without ethics review"},
        {"node_id": "D", "response": "Store every consensus record in Memory Mycelium"},
        {"node_id": "E", "response": "Use 3-6-9 vortex geometry for tie-breaking"},
        {"node_id": "F", "response": "Reject nodes outside golden band automatically"},
    ]
    result = v.achieve_consensus("How should the public LYGO stack evolve?", responses)
    print(json.dumps(result, indent=2, default=str))