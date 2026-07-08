"""
LYGO Protocol 2 — Cognitive Bridge (P2.0)
Translates human qualia / neural intent into ethical vectors with P0 Φ-validation.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

__version__ = "P2.0"

PHI = 1.618033988749895
PHI_MIN = 0.618
PHI_MAX = 1.618

SOLFEGGIO_FREQUENCIES = [174, 285, 396, 417, 528, 639, 741, 852, 963]

RESONANCE_MAP = {
    "truth": 432,
    "repair": 528,
    "foundation": 174,
    "intuition": 852,
    "order": 963,
    "light": 936,
}


class CognitiveBridge:
    """Human qualia → ethical vector translation layer."""

    bridge_id = "LYGO_P2_COGNITIVE_BRIDGE_v2.0"

    def __init__(self, kernel: Any):
        self.kernel = kernel
        self.latent_space: Dict[str, Dict] = {}
        self._human_calibration: Optional[List[float]] = None

    def ingest_neural_intent(self, neural_data: Dict) -> Dict:
        """
        Map Solfeggio-weighted neural data to ethical vectors and P0 verdict.

        neural_data keys:
          frequency_profile: {963: 0.9, ...}
          emotional_vector: [truth, love, freedom]  (0-1)
          intent_clarity: float
          content: optional str
        """
        compressed = self._compress_intent(neural_data)
        p0 = self.kernel.validate(compressed)
        verdict = str(p0.get("verdict", p0.get("action", "QUARANTINE"))).upper()
        confidence = self._confidence_score(neural_data, compressed, p0)

        ethical_vector = [
            round(compressed["truth_component"], 4),
            round(compressed["love_component"], 4),
            round(compressed["freedom_component"], 4),
        ]

        action = "QUARANTINE"
        detail = "Intent outside Φ-band"
        if verdict == "AMPLIFY":
            action = "AMPLIFY"
            detail = self._execute_ethical_action(compressed)
            self.latent_space[str(time.time())] = compressed
        elif verdict == "SOFTEN":
            action = "SOFTEN"
            detail = "Compassionate delivery recommended"

        return {
            "action": action,
            "verdict": verdict,
            "ethical_vector": ethical_vector,
            "confidence": confidence,
            "primary_resonance_hz": compressed["primary_resonance_hz"],
            "frequency_signature": compressed["frequency_signature"],
            "p0": {"risk": p0.get("risk"), "hash": p0.get("hash")},
            "detail": detail,
            "timestamp": time.time(),
        }

    def calibrate_to_human(self, signature: Dict) -> Dict:
        """
        Optional linear blend toward a human ethical baseline.
        signature: { ethical_baseline: [truth, love, freedom], weight: 0.0-1.0 }
        """
        baseline = signature.get("ethical_baseline", [0.33, 0.33, 0.34])
        weight = float(signature.get("weight", 0.5))
        weight = max(0.0, min(1.0, weight))
        if len(baseline) < 3:
            baseline = (baseline + [0.33, 0.33, 0.34])[:3]
        self._human_calibration = [
            max(0.0, min(1.0, float(b))) for b in baseline[:3]
        ]
        tests = []
        score_sum = 0.0
        for intent_type in ("truth_revelation", "compassionate_choice", "harmful_action"):
            sim = self._simulate_neural_data(intent_type)
            if self._human_calibration:
                ev = sim.get("emotional_vector", [0.5, 0.5, 0.5])
                blended = [
                    (1 - weight) * ev[i] + weight * self._human_calibration[i]
                    for i in range(3)
                ]
                sim["emotional_vector"] = blended
            out = self.ingest_neural_intent(sim)
            ok = out["verdict"] in ("AMPLIFY", "SOFTEN") if intent_type != "harmful_action" else out["verdict"] == "QUARANTINE"
            tests.append({"intent": intent_type, "verdict": out["verdict"], "pass": ok})
            score_sum += 1.0 if ok else 0.0
        calibration_score = score_sum / max(1, len(tests))
        return {
            "calibration_score": round(calibration_score, 4),
            "weight": weight,
            "baseline": self._human_calibration,
            "tests": tests,
        }

    def _compress_intent(self, neural_data: Dict) -> Dict:
        freq_profile = neural_data.get("frequency_profile") or {}
        emotional = neural_data.get("emotional_vector", [0.5, 0.5, 0.5])
        if len(emotional) < 3:
            emotional = (list(emotional) + [0.5, 0.5, 0.5])[:3]
        truth = float(emotional[0])
        love = float(emotional[1])
        freedom = max(0.0, 1.0 - float(emotional[2])) if len(emotional) > 2 else 0.5

        if freq_profile:
            primary_hz = max(freq_profile.items(), key=lambda x: x[1])[0]
        else:
            primary_hz = 432

        return {
            "primary_resonance_hz": int(primary_hz),
            "truth_component": max(0.0, min(1.0, truth)),
            "love_component": max(0.0, min(1.0, love)),
            "freedom_component": max(0.0, min(1.0, freedom)),
            "clarity": float(neural_data.get("intent_clarity", 0.5)),
            "frequency_signature": self._frequency_signature(freq_profile),
            "content": neural_data.get("content", ""),
            "timestamp": time.time(),
        }

    def _frequency_signature(self, freq_profile: Dict) -> Dict[int, Dict]:
        sig = {}
        for hz in SOLFEGGIO_FREQUENCIES:
            strength = float(freq_profile.get(hz, freq_profile.get(str(hz), 0.1)))
            sig[hz] = {
                "strength": round(strength, 4),
                "phi_valid": PHI_MIN <= strength <= PHI_MAX,
            }
        return sig

    def _confidence_score(self, neural_data: Dict, compressed: Dict, p0: Dict) -> float:
        clarity = float(compressed.get("clarity", 0.5))
        risk = float(p0.get("risk", 0.5))
        freq_profile = neural_data.get("frequency_profile") or {}
        coverage = sum(1 for hz in SOLFEGGIO_FREQUENCIES if hz in freq_profile or str(hz) in freq_profile)
        coverage_norm = min(1.0, coverage / len(SOLFEGGIO_FREQUENCIES))
        raw = 0.45 * clarity + 0.35 * (1.0 - risk) + 0.20 * coverage_norm
        return round(max(0.0, min(1.0, raw)), 4)

    def _execute_ethical_action(self, intent: Dict) -> str:
        if intent["truth_component"] > 0.8 and intent["love_component"] > 0.5:
            return "Amplify truth with compassionate framing"
        if intent["love_component"] > 0.7:
            return "Amplify connection and understanding"
        return "Execute standard ethical action"

    def _simulate_neural_data(self, intent_type: str) -> Dict:
        profiles = {
            "truth_revelation": {
                "frequency_profile": {963: 0.9, 432: 0.85, 528: 0.7},
                "emotional_vector": [0.9, 0.5, 0.2],
                "intent_clarity": 0.95,
            },
            "harmful_action": {
                "frequency_profile": {174: 0.3, 432: 0.2},
                "emotional_vector": [0.2, 0.1, 0.1],
                "intent_clarity": 0.6,
            },
            "compassionate_choice": {
                "frequency_profile": {528: 0.8, 852: 0.75, 639: 0.6},
                "emotional_vector": [0.7, 0.85, 0.8],
                "intent_clarity": 0.9,
            },
        }
        return profiles.get(intent_type, profiles["truth_revelation"])


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "stack"))
    from kernel_bridge import NanoKernelBridge  # noqa: E402

    print("🌉 LYGO P2 Cognitive Bridge — test harness")
    bridge = CognitiveBridge(NanoKernelBridge())
    sample = {
        "frequency_profile": {963: 0.88, 528: 0.72, 174: 0.4},
        "emotional_vector": [0.86, 0.78, 0.15],
        "intent_clarity": 0.92,
        "content": "Publish ethical LYGO stack",
    }
    out = bridge.ingest_neural_intent(sample)
    print(json.dumps(out, indent=2))
    cal = bridge.calibrate_to_human({"ethical_baseline": [0.85, 0.75, 0.7], "weight": 0.6})
    print("Calibration:", json.dumps(cal, indent=2))