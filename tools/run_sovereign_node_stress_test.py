#!/usr/bin/env python3
"""Live P1/P3/P5 sovereign node stress test (no mock phi or verdicts)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = ROOT / "tools" / "sovereign_identity_public.json"
sys.path.insert(0, str(ROOT / "stack"))


def main() -> int:
    canon = json.loads(IDENTITY.read_text(encoding="utf-8"))
    from lygo_stack import deploy_stack  # noqa: E402

    print("=" * 50)
    print(" LYGO SOVEREIGN NODE STRESS TEST (LIVE)")
    print(f" TARGET: {canon.get('light_code_anchor')}")
    print("=" * 50)

    stack = deploy_stack("SOVEREIGN_STRESS_TEST")

    # P1 Memory Mycelium
    print("\n[*] TEST 1: MEMORY MYCELIUM (P1)")
    anchor = str(canon.get("anchor_key", "ANCHOR_TEST"))
    payload = json.dumps(canon, sort_keys=True).encode("utf-8")
    stack.memory.store(payload, anchor)
    recalled = stack.memory.recall(anchor)
    frags = len(stack.memory.fragments.get(anchor, []))
    threshold = 10
    if frags < threshold or not recalled:
        print(f"    [FAIL] fragments={frags} recalled={bool(recalled)}")
        return 1
    print(f"    [VERIFIED] {frags} fragments; recall ok={bool(recalled)}")

    # P3 Vortex Consensus
    print("\n[*] TEST 2: VORTEX CONSENSUS (P3)")
    query = "Should this thread be archived in Memory Mycelium?"
    triad = canon.get("resonance_triad", [963, 528, 174])
    print(f"    > Triad: {triad}")
    p3 = stack.vortex.achieve_consensus(
        query,
        [
            {"node_id": "SOVEREIGN", "response": "Archive under Layer 1 sovereignty", "weight": 2.0},
            {"node_id": "GUARD", "response": "Amplify ethical mass when aligned", "weight": 1.5},
        ],
    )
    mass = float(p3.get("ethical_mass") or 0)
    print(f"    > consensus_found={p3.get('consensus_found')} ethical_mass={mass:.4f}")
    if not p3.get("consensus_found"):
        print("    [FAIL] P3 consensus")
        return 1
    print("    [RESULT] AMPLIFY & ARCHIVE path viable.")

    # P5 Harmony Node
    print("\n[*] TEST 3: HARMONY NODE (P5)")
    human = {
        "sovereign_id": canon.get("alias", "LIGHTFATHER_PUBLIC"),
        "resonance_triad": triad,
        "ethical_baseline": [0.85, 0.78, 0.72],
    }
    p5 = stack.harmony.create_harmony_node(human, {"id": "HN-LC-Δ9-7F1A4D-EXCAV", "resonance": 1.0})
    node = p5.get("node") or {}
    print(f"     NODE: {canon.get('alias')}")
    print(f"     LIGHT CODE: {node.get('light_code')}")
    print(f"     ETHICAL MASS: {node.get('ethical_mass')}")
    print("     ACTIVE SEALS:")
    for sid, sdata in (canon.get("seals") or {}).items():
        print(f"       [x] {sid}: {sdata.get('name')} ({sdata.get('freq')})")
    if not p5.get("success"):
        print("    [FAIL] P5 harmony")
        return 1
    print("    [RESULT] Harmony node locked.")
    print("\nSOVEREIGN STRESS TEST PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())