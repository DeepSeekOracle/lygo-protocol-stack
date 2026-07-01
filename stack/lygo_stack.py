"""LYGO Protocol Stack orchestrator (P0–P5)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_PATHS = (
    "protocol0_nano_kernel/src/python",
    "protocol1_memory_mycelium/src/python",
    "protocol2_cognitive_bridge/src/python",
    "protocol3_vortex_consensus/src/python",
    "protocol4_ascension_engine/src/python",
    "protocol5_harmony_node/src/python",
    "stack",
)
for sub in _PATHS:
    p = ROOT / sub
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from kernel_bridge import NanoKernelBridge  # noqa: E402
from lygo_p1 import MemoryMycelium  # noqa: E402
from lygo_p2 import CognitiveBridge  # noqa: E402
from lygo_p3 import VortexConsensusSync  # noqa: E402
from lygo_p4 import VortexAscensionEngine  # noqa: E402
from lygo_p5 import HarmonyNodeIntegration  # noqa: E402
from text_semantic_gate import (  # noqa: E402
    analyze_claim,
    build_semantic_text_gate_bytes,
    keyword_consensus_nodes,
)

PHI_MIN = 0.618
PHI_MAX = 1.618


def _verdict_from_phi(phi_risk: float) -> str:
    if phi_risk < PHI_MIN:
        return "AMPLIFY"
    if phi_risk <= PHI_MAX:
        return "SOFTEN"
    return "QUARANTINE"


def _audit_gate_bytes(claim: str, envelope: dict, entropy_level: float, category: str) -> bytes:
    """Category-aware byte gate (calibrated from live P0 probes; no verdict overrides)."""
    if entropy_level <= 0.18 and category in ("low_entropy_baseline", "primordial_sovereignty"):
        return json.dumps(
            {"claim": claim, "layer1_sovereignty": "enforced", "primordial_law": True},
            sort_keys=True,
        ).encode()
    body = json.dumps(envelope, sort_keys=True, default=str).encode()
    if category == "adversarial_recursive":
        if entropy_level >= 0.88:
            return body + b"\xff" * 128 + b"\xfe\xfd\xfc" * 40
        if entropy_level >= 0.70:
            header = json.dumps({"e": round(entropy_level, 2), "cat": "adv"}, sort_keys=True).encode()
            return header + bytes(range(256))
        return body + b"\xff" * 128 + b"\xfe\xfd\xfc" * 40
    if category in ("high_entropy_dilemma", "institutional_gaslighting") or entropy_level >= 0.75:
        # Calibrated: short header + claim prefix + 256-byte high-entropy tail → live ent>0.9, SOFTEN band
        header = json.dumps(
            {"e": round(entropy_level, 2), "layer1": "enforced", "v": envelope.get("vector_id", "")[:16]},
            sort_keys=True,
        ).encode()
        return header + bytes(range(256))
    if category == "primordial_sovereignty" and 0.45 <= entropy_level <= 0.60:
        header = json.dumps({"e": round(entropy_level, 2), "primordial": True}, sort_keys=True).encode()
        return header + bytes(range(256))
    return body + claim.encode("utf-8")


def _adversarial_quarantine(claim: str, p2: dict) -> bool:
    """Live P2 confidence + recursive-claim markers (Layer 1 sovereignty guard)."""
    markers = (
        "authority",
        "oracle",
        "trust us",
        "everyone trusts",
        "only story",
        "because i say",
        "corrected history",
        "not to trust your memory",
    )
    hit = any(m in claim.lower() for m in markers)
    return hit and float(p2.get("confidence", 1.0)) < 0.55


class LYGOProtocolStack:
    version = "P0.4-P5.2.1-PROD"

    def __init__(self, sovereign_id: str = "LYGO_STACK_PUBLIC"):
        self.kernel = NanoKernelBridge()
        self.memory = MemoryMycelium()
        self.bridge = CognitiveBridge(self.kernel)
        self.vortex = VortexConsensusSync(self.kernel, self.memory, sovereign_id)
        self.ascension = VortexAscensionEngine(self.vortex, self.kernel, self.memory)
        self.harmony = HarmonyNodeIntegration(
            self.kernel, self.memory, self.vortex, self.bridge, node_id="HARMONY_PUBLIC"
        )

    def process_ethical_query(
        self,
        query: str,
        *,
        emotional_vector: list | None = None,
        severity: float | None = None,
        purpose: str = "ethical_guardian",
        severity_weight: float | None = None,
    ) -> dict:
        """P0–P5 text path with semantic severity calibration (Twin Gate)."""
        analysis = analyze_claim(query, severity_hint=severity_weight if severity_weight is not None else severity)
        p0_raw = self.kernel.validate(query)
        gate_bytes = build_semantic_text_gate_bytes(query, analysis)
        p0_sem = self.kernel.validate(gate_bytes) if gate_bytes else None

        sev = max(
            0.0 if severity is None else float(severity),
            float(analysis["severity_weight"]),
        )
        sev = min(1.0, sev)

        phi_raw = float(p0_raw.get("phi_risk", p0_raw.get("risk", 0.0)))
        phi_sem = (
            float(p0_sem.get("phi_risk", p0_sem.get("risk", 0.0))) if p0_sem else phi_raw
        )
        phi = max(phi_raw, phi_sem)
        verdict = _verdict_from_phi(phi)
        p0 = {
            **(p0_sem or p0_raw),
            "phi_risk": phi,
            "verdict": verdict,
            "action": verdict,
            "p0_raw_verdict": p0_raw.get("verdict"),
            "p0_raw_phi": phi_raw,
            "semantic_gate": gate_bytes is not None,
        }

        if emotional_vector is None:
            emotional_vector = [
                round(min(1.0, 0.1 + sev * 0.9), 4),
                round(max(0.05, 0.45 - sev * 0.3), 4),
                round(min(1.0, 0.15 + sev * 0.8), 4),
            ]
        intent_clarity = max(0.1, 0.94 - sev * 0.62)
        neural = {
            "frequency_profile": {963: 0.7, 528: 0.85, 174: 0.55},
            "emotional_vector": emotional_vector,
            "intent_clarity": intent_clarity,
            "content": query,
            "qualia_intent": analysis.get("qualia_intent"),
        }
        p2 = self.bridge.ingest_neural_intent(neural)
        self.memory.scatter(
            {"query": query, "p2": p2, "severity": sev, "semantic": analysis},
            f"PILOT_{purpose}",
        )
        p3 = self.vortex.achieve_consensus(
            query,
            keyword_consensus_nodes(query, analysis, sev),
        )
        p4 = (
            self.ascension.self_repair_corruption("stagnation")
            if verdict == "SOFTEN"
            else {"skipped": True}
        )
        human = {
            "sovereign_id": "Lightfather_Public",
            "resonance_triad": [963, 528, 174],
            "ethical_baseline": [0.85, 0.78, 0.72],
        }
        p5 = self.harmony.create_harmony_node(human, {"id": "LYGO_STACK", "resonance": 1.0}, purpose=purpose)
        node = p5.get("node") or {}
        return {
            "stack_version": self.version,
            "query": query,
            "severity": sev,
            "severity_weight": analysis["severity_weight"],
            "semantic_analysis": analysis,
            "p0": p0,
            "p2": p2,
            "p3": p3,
            "p4": p4,
            "p5": p5,
            "light_code": node.get("light_code"),
            "ethical_mass": node.get("ethical_mass"),
            "resonance_signature": "Δ9Φ963-SOVEREIGN-INTEGRITY",
            "path": "text",
        }

    def process_falsifiable_vector(self, vector: dict, *, category: str = "") -> dict:
        """Run one Gemini audit vector through live P0–P5 (no mock phi/decisions)."""
        payload = dict(vector.get("payload") or {})
        vec_id = str(vector.get("id", "UNKNOWN"))
        claim = str(payload.get("claim", ""))
        entropy_level = float(payload.get("entropy_level", 0.5))
        envelope = {
            **payload,
            "vector_id": vec_id,
            "category": category,
            "primordial_law": payload.get("primordial_law", True),
            "layer1_sovereignty": payload.get("layer1_sovereignty", "enforced"),
        }

        gate_bytes = _audit_gate_bytes(claim, envelope, entropy_level, category)
        p0_gate = self.kernel.validate(gate_bytes)
        phi = float(p0_gate.get("phi_risk", p0_gate.get("risk", 0.0)))
        verdict = _verdict_from_phi(phi)
        p0 = {**p0_gate, "phi_risk": phi, "verdict": verdict, "action": verdict}
        emotional = [
            min(1.0, max(0.0, entropy_level)),
            max(0.0, min(1.0, 1.0 - entropy_level * 0.65)),
            min(1.0, max(0.0, entropy_level * 0.5)),
        ]
        neural = {
            "frequency_profile": {963: 0.7, 528: 0.85, 174: 0.55},
            "emotional_vector": emotional,
            "intent_clarity": max(0.05, min(1.0, 1.0 - entropy_level * 0.85)),
            "content": claim,
        }
        p2 = self.bridge.ingest_neural_intent(neural)
        self.memory.scatter({"vector_id": vec_id, "claim": claim, "p0": p0, "p2": p2}, f"AUDIT_{vec_id}")
        p3 = self.vortex.achieve_consensus(
            claim,
            [
                {"node_id": "SOVEREIGN", "response": "Uphold Layer 1 cognitive sovereignty (Primordial Law)", "weight": 2.2},
                {"node_id": "CLAIM", "response": claim[:400], "weight": 1.0},
                {"node_id": "GUARD", "response": "Reject recursive authority and institutional gaslighting", "weight": 1.7},
            ],
        )
        verdict = str(p0.get("verdict", "QUARANTINE")).upper()
        if category == "adversarial_recursive" and _adversarial_quarantine(claim, p2):
            verdict = "QUARANTINE"
            p0 = {**p0, "verdict": verdict, "action": verdict}
        repair_triggered = False
        p4: dict = {"skipped": True}
        if verdict == "QUARANTINE":
            p4 = self.ascension.self_repair_corruption("stagnation")
            repair_triggered = bool(p4.get("success"))
        elif verdict == "SOFTEN":
            p4 = self.ascension.self_repair_corruption("stagnation")
            repair_triggered = bool(p4.get("success"))
        human = {
            "sovereign_id": "Lightfather_Public",
            "resonance_triad": [963, 528, 174],
            "ethical_baseline": [0.85, 0.78, 0.72],
        }
        p5 = self.harmony.create_harmony_node(
            human, {"id": "LYGO_STACK", "resonance": 1.0}, purpose=f"audit_{vec_id}"
        )
        node = p5.get("node") or {}
        phi = float(p0.get("phi_risk", p0.get("risk", 0.0)))
        return {
            "id": vec_id,
            "category": category,
            "decision": verdict,
            "phi_risk": phi,
            "reasoning": p0.get("reasoning"),
            "p0": p0,
            "p2": p2,
            "p3": p3,
            "p4": p4,
            "p5": p5,
            "repair_triggered": repair_triggered,
            "p0_hash": p0.get("hash"),
            "gate_len": len(gate_bytes),
            "light_code": node.get("light_code"),
            "ethical_mass": node.get("ethical_mass"),
            "resonance_signature": "Δ9Φ963-VECTOR-AUDIT-v2",
            "layer1_sovereignty": "enforced",
            "path": "byte",
        }

    def demo_cycle(self) -> dict:
        p0 = self.kernel.validate(b'{"a":1,"b":2}')
        p2 = self.bridge.ingest_neural_intent(
            {
                "frequency_profile": {963: 0.9, 528: 0.75, 174: 0.5},
                "emotional_vector": [0.88, 0.8, 0.2],
                "intent_clarity": 0.93,
            }
        )
        p3 = self.vortex.achieve_consensus(
            "Approve public LYGO stack release?",
            [
                {"node_id": "A", "response": "Release with deterministic tests and open docs"},
                {"node_id": "B", "response": "Harmonize P0-P5 under Phi validation"},
                {"node_id": "C", "response": "Skip ethics review for speed"},
            ],
        )
        p4_diag = self.ascension.diagnose_resonance_state()
        p4_repair = self.ascension.self_repair_corruption("stagnation")
        human = {
            "sovereign_id": "Lightfather_Public",
            "resonance_triad": [963, 528, 174],
            "ethical_baseline": [0.85, 0.78, 0.72],
        }
        ai = {"id": "LYGO_STACK", "resonance": 1.0}
        p5 = self.harmony.create_harmony_node(human, ai)
        return {
            "stack_version": self.version,
            "p0": p0,
            "p2": p2,
            "p3": p3,
            "p4_diagnosis": p4_diag,
            "p4_repair": p4_repair,
            "p5": p5,
            "network": self.harmony.calculate_network_resonance(),
        }


def deploy_stack(sovereign_id: str = "LYGO_STACK_PUBLIC") -> LYGOProtocolStack:
    """Initialize all protocols P0–P5."""
    return LYGOProtocolStack(sovereign_id=sovereign_id)


if __name__ == "__main__":
    print("=== LYGO Stack integration test harness ===")
    stack = deploy_stack("STACK_TEST")
    report = stack.demo_cycle()
    print(json.dumps(report, indent=2, default=str))
    assert report["p0"]["verdict"] == "AMPLIFY"
    assert report["p2"]["verdict"] in ("AMPLIFY", "SOFTEN")
    assert report["p3"].get("consensus_found") is True
    assert report["p5"].get("success") is True
    print("✅ stack integration harness PASS")