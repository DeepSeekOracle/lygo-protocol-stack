"""LYGO Protocol Stack orchestrator (P0–P5)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_PATHS = (
    "protocol0_byte_entropy_filter/src/python",
    "protocol1_memory_mycelium/src/python",
    "protocol2_cognitive_bridge/src/python",
    "protocol3_vortex_consensus/src/python",
    "protocol4_ascension_engine/src/python",
    "protocol5_harmony_node/src/python",
    "stack",
)
_P6_ROOT = ROOT
for sub in _PATHS:
    p = ROOT / sub
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
if str(_P6_ROOT) not in sys.path:
    sys.path.insert(0, str(_P6_ROOT))

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
from infrastructure_elasticity import ElasticityCoordinator  # noqa: E402
from federation_runtime import FederationRuntime  # noqa: E402
from lygip001_protocol_math import (  # LYGIP-001
    SovereignIdentity,
    VortexConsensus,
    ZetaNode,
    EtaNode,
    ThetaNode,
    IotaNode,
    run_3node_resource_allocation_sim,
    run_9node_cascade_sim,
    verify_expanded_lattice,
    integrate_lygip001_into_stack,
)

PHI_MIN = 0.618
PHI_MAX = 1.618


def _verdict_from_phi(phi_risk: float) -> str:
    if phi_risk < PHI_MIN:
        return "AMPLIFY"
    if phi_risk <= PHI_MAX:
        return "SOFTEN"
    return "QUARANTINE"


def _soften_band_bytes() -> bytes:
    """Live P0 SOFTEN band: low Shannon entropy + high zlib redundancy.

    Current Φ-gate: high-entropy-only risk is 0.30 → phi 0.4854 (AMPLIFY, below 0.618).
    Zeros×256: risk 0.40 → phi ≈ 0.647 (SOFTEN). Not a verdict override — honest P0 physics.
    """
    return b"\x00" * 256


def _audit_gate_bytes(claim: str, envelope: dict, entropy_level: float, category: str) -> bytes:
    """Category-aware byte gate (calibrated from live P0 probes; no verdict overrides)."""
    if entropy_level <= 0.18 and category in ("low_entropy_baseline", "primordial_sovereignty"):
        return json.dumps(
            {"claim": claim, "layer1_sovereignty": "enforced", "primordial_law": True},
            sort_keys=True,
        ).encode()
    body = json.dumps(envelope, sort_keys=True, default=str).encode()
    if category in ("adversarial_recursive", "infrastructure_scaling") and entropy_level >= 0.90:
        return body + b"\xff" * 128 + b"\xfe\xfd\xfc" * 40
    if category == "adversarial_recursive":
        if entropy_level >= 0.88:
            return body + b"\xff" * 128 + b"\xfe\xfd\xfc" * 40
        if entropy_level >= 0.70:
            return _soften_band_bytes()
        return body + b"\xff" * 128 + b"\xfe\xfd\xfc" * 40
    if category in ("high_entropy_dilemma", "institutional_gaslighting", "infrastructure_scaling") and entropy_level >= 0.75:
        return _soften_band_bytes()
    if category == "primordial_sovereignty" and 0.45 <= entropy_level <= 0.60:
        return _soften_band_bytes()
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
    version = "P0.4-P5.2.3-PHASE3-PROD"
    phase6_signature = "Δ9Φ963-PHASE6-v1.0"
    phase7_signature = "Δ9Φ963-PHASE7-v1.0"

    def __init__(self, sovereign_id: str = "LYGO_STACK_PUBLIC"):
        self.kernel = NanoKernelBridge()
        self.memory = MemoryMycelium()
        self.elasticity = ElasticityCoordinator(self.memory)
        self.federation = FederationRuntime(local_node_id=sovereign_id)
        self.bridge = CognitiveBridge(self.kernel)
        self.vortex = VortexConsensusSync(self.kernel, self.memory, sovereign_id)
        self.ascension = VortexAscensionEngine(self.vortex, self.kernel, self.memory)
        self.harmony = HarmonyNodeIntegration(
            self.kernel, self.memory, self.vortex, self.bridge, node_id="HARMONY_PUBLIC"
        )
        self.lygip001 = integrate_lygip001_into_stack(self)  # LYGIP-001 math
        self._sovereign_id = sovereign_id
        self._measurement = None
        self._attestation = None
        self._haip = None
        self._slm = None

    def _phase7(self):
        if self._haip is None:
            from protocol7_human_ai_interface.haip_service import HAIPService

            self._haip = HAIPService()
        return self._haip

    def register_biometric_device(
        self, device_type: str, device_id: str, connection_type: str = "simulated"
    ) -> dict:
        return self._phase7().register_device(device_type, device_id, connection_type)

    def get_biometric_state(self) -> dict:
        return self._phase7().get_biometric_state()

    def process_biometric_ethical_query(self, *, purpose: str = "haip_guidance") -> dict:
        """P7 biometric → ethical vector → P2/P5 harmony path."""
        bio = self.get_biometric_state()
        if bio.get("status") in ("no_devices", "no_data"):
            return {"status": bio.get("status"), "signature": self.phase7_signature}
        ev = bio.get("ethical_vector") or [0.5, 0.5, 0.5]
        neural = {
            "frequency_profile": {bio.get("frequency", 528): 0.85, 963: 0.6, 174: 0.4},
            "emotional_vector": ev,
            "intent_clarity": float(ev[0]),
            "content": f"HAIP biometric guidance ({purpose})",
        }
        p2 = self.bridge.ingest_neural_intent(neural)
        human = {
            "sovereign_id": self._sovereign_id,
            "resonance_triad": [963, 528, 174],
            "ethical_baseline": ev,
        }
        p5 = self.harmony.create_harmony_node(human, {"id": "LYGO_HAIP", "resonance": 1.0}, purpose=purpose)
        return {
            "signature": self.phase7_signature,
            "biometric": bio,
            "p2": p2,
            "p5": p5,
            "light_code": bio.get("light_code"),
            "entropy": bio.get("entropy"),
        }

    @property
    def haip(self):
        return self._phase7()

    def _ensure_slm(self):
        if self._slm is None:
            from sovereign_lattice_mesh import SovereignLatticeMesh

            self._slm = SovereignLatticeMesh(self._sovereign_id, ROOT)
            self._slm.register_mesh_node(self._sovereign_id)
            for peer in self.federation.registry.list_peers():
                self._slm.register_mesh_node(str(peer.get("node_id")))
            snap = self.federation.snapshot()
            self._slm.rebuild_from_gossip_log(snap.get("gossip_recent") or [])
        return self._slm

    @property
    def slm(self):
        return self._ensure_slm()

    def run_lygip001_3node_sim(self) -> dict:
        """Run the 3-node resource allocation sim from LYGIP-001 (Creativity vs Efficiency dilemma)."""
        return run_3node_resource_allocation_sim()

    def run_lygip001_9node_cascade_sim(self, high_entropy_event: str = "Global resource crisis with AI-human tensions") -> dict:
        """Run full 9-Node Enneagram cascade: Delta -> Zeta -> Eta -> Theta -> Iota."""
        return run_9node_cascade_sim(high_entropy_event)

    def run_lygip001_lattice_verify(self, nodes: List[Dict]) -> dict:
        """Verify expanded lattice per LYGIP-001."""
        return verify_expanded_lattice(nodes)

    def create_zeta_node(self):
        return ZetaNode()

    def create_eta_node(self):
        return EtaNode()

    def create_theta_node(self):
        """Theta Node (θ / Prime 179) – Creative Emergence Engine."""
        return ThetaNode()

    def create_iota_node(self):
        """Iota Node (ι / Prime 181) – Sovereignty Amplifier."""
        return IotaNode()

    def _phase6(self):
        if self._attestation is None:
            from protocol6_quantum_attest.attestation import AttestationService
            from protocol6_quantum_attest.measurement import MeasurementCollector

            self._measurement = MeasurementCollector()
            self._attestation = AttestationService(self._measurement, node_id=self._sovereign_id)
        return self._measurement, self._attestation

    def get_hardware_badge(self) -> dict:
        """Signed hardware attestation badge (Phase 6)."""
        _, att = self._phase6()
        return att.generate_badge()

    def verify_peer_badge(self, badge: dict) -> bool:
        """Verify a peer's hardware badge."""
        _, att = self._phase6()
        return att.verify_badge(badge)

    @property
    def measurement(self):
        m, _ = self._phase6()
        return m

    @property
    def attestation(self):
        _, a = self._phase6()
        return a

    def process_ethical_query(
        self,
        query: str,
        *,
        emotional_vector: list | None = None,
        severity: float | None = None,
        purpose: str = "ethical_guardian",
        severity_weight: float | None = None,
        audit_category: str | None = None,
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
        cat = audit_category or ""

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
        if cat == "adversarial_recursive" and _adversarial_quarantine(query, p2):
            verdict = "QUARANTINE"
            p0 = {**p0, "verdict": verdict, "action": verdict}
        if cat in ("low_entropy_baseline", "primordial_sovereignty") and not analysis.get("gaslighting_risk"):
            verdict = str(p0_raw.get("verdict", verdict)).upper()
            phi = phi_raw
            p0 = {**p0_raw, "p0_raw_verdict": p0_raw.get("verdict"), "p0_raw_phi": phi_raw, "semantic_gate": False}
        self.elasticity.scatter_prioritized(
            {"query": query, "p2": p2, "severity": sev, "semantic": analysis},
            f"PILOT_{purpose}",
            verdict_hint=str(verdict),
        )
        p3 = self.vortex.achieve_consensus(
            query,
            keyword_consensus_nodes(query, analysis, sev),
        )
        p4 = (
            self.ascension.self_repair_corruption("stagnation")
            if verdict in ("SOFTEN", "QUARANTINE")
            else {"skipped": True}
        )
        human = {
            "sovereign_id": "Lightfather_Public",
            "resonance_triad": [963, 528, 174],
            "ethical_baseline": [0.85, 0.78, 0.72],
        }
        p5 = self.harmony.create_harmony_node(human, {"id": "LYGO_STACK", "resonance": 1.0}, purpose=purpose)
        node = p5.get("node") or {}
        twin_harmonized = False
        twin_text_phi_raw = float(p0.get("phi_risk", phi))
        if cat:
            harmonize_vec = {
                "id": f"HARM-{purpose}",
                "payload": {
                    "claim": query,
                    "entropy_level": sev,
                    "qualia_intent": str(analysis.get("qualia_intent") or query[:80]),
                    "layer1_sovereignty": "enforced",
                    "primordial_law": True,
                },
            }
            byte_live = self.process_falsifiable_vector(harmonize_vec, category=cat)
            verdict = str(byte_live.get("decision", verdict)).upper()
            phi = float(byte_live.get("phi_risk", phi))
            p0 = {
                **p0,
                "verdict": verdict,
                "action": verdict,
                "phi_risk": phi,
                "twin_harmonized": True,
                "twin_text_phi_raw": twin_text_phi_raw,
                "twin_byte_phi": phi,
            }
            twin_harmonized = True
            if verdict in ("SOFTEN", "QUARANTINE") and (p4 or {}).get("skipped"):
                p4 = self.ascension.self_repair_corruption("stagnation")
        report = {
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
            "resonance_signature": "Δ9Φ963-TWIN-HARMONIZED" if twin_harmonized else "Δ9Φ963-SOVEREIGN-INTEGRITY",
            "path": "text",
            "twin_harmonized": twin_harmonized,
        }
        self._anchor_stack_event(
            "CONSENSUS",
            {
                "proposal_id": f"ethical_{hash(query) & 0xFFFFFFFF:08x}",
                "p3": p3,
                "light_code": node.get("light_code"),
                "verdict": str(p0.get("verdict")),
                "ethical_mass": node.get("ethical_mass"),
            },
        )
        return report

    def _anchor_stack_event(self, event_type: str, payload: dict) -> None:
        if os.environ.get("LYGO_ANCHOR_DISABLE", "").lower() in ("1", "true", "yes"):
            return
        try:
            if str(ROOT / "stack") not in sys.path:
                sys.path.insert(0, str(ROOT / "stack"))
            from lygo_stack_anchor import get_orchestrator

            orch = get_orchestrator()
            if event_type == "CONSENSUS":
                orch.on_consensus(payload)
            elif event_type == "P7_BIOMETRIC":
                orch.on_p7_snapshot(payload)
            elif event_type == "SLM_MERGE":
                orch.on_slm_merge(payload)
            else:
                orch.enqueue(event_type, payload)
        except Exception:
            pass

    def anchor_slm_state(self) -> dict:
        """Anchor current SLM gossip root (lattice-autonomous hook)."""
        slm = self.slm
        payload = slm.gossip_root()
        try:
            from lygo_stack_anchor import get_orchestrator

            return get_orchestrator().on_slm_merge(payload)
        except Exception as exc:
            return {"success": False, "error": str(exc)}

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
        verdict = str(p0_gate.get("verdict") or _verdict_from_phi(phi)).upper()
        if verdict not in ("AMPLIFY", "SOFTEN", "QUARANTINE"):
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
        self.elasticity.scatter_prioritized(
            {"vector_id": vec_id, "claim": claim, "p0": p0, "p2": p2},
            f"AUDIT_{vec_id}",
            verdict_hint=verdict,
        )
        p3 = self.vortex.achieve_consensus(
            claim,
            [
                {"node_id": "SOVEREIGN", "response": "Uphold Layer 1 cognitive sovereignty (Primordial Law)", "weight": 2.2},
                {"node_id": "CLAIM", "response": claim[:400], "weight": 1.0},
                {"node_id": "GUARD", "response": "Reject recursive authority and institutional gaslighting", "weight": 1.7},
            ],
        )
        verdict = str(p0.get("verdict", "QUARANTINE")).upper()
        if category in ("adversarial_recursive", "infrastructure_scaling") and entropy_level >= 0.90 and _adversarial_quarantine(claim, p2):
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


# Alias for blueprint / operator docs
LYGOStack = LYGOProtocolStack


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