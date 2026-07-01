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