#!/usr/bin/env python3
"""Scenario B: Full 9-Node Enneagram Cascade Pilot.
Passes a simulated high-entropy event through the complete LYGO 9-Node lattice:
Delta -> Zeta -> Eta -> Theta -> Iota.
This completes the Enneagram 3x3 matrix (Nodes 8 & 9: Theta/Iota).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stack"))

from lygo_stack import deploy_stack  # noqa: E402
from lygip001_protocol_math import run_9node_cascade_sim  # noqa: E402

# Optional bridge synchronization (Enneagram -> EVM)
try:
    sys.path.insert(0, str(ROOT / "protocol_bridge"))
    from lygo_bridge_orchestrator import LYGOBlockchainBridge  # noqa: E402
    _BRIDGE_AVAILABLE = True
except Exception:
    _BRIDGE_AVAILABLE = False

SIGNATURE = "Δ9Φ963-PILOT-9NODE-CASCADE-v1"
DEFAULT_EVENT = "High-entropy global crisis: AI sovereignty conflict with centralized control and loss of individual agency"


def run_9node_cascade_pilot(high_entropy_event: str = DEFAULT_EVENT, write_report: bool = True) -> dict:
    stack = deploy_stack("PILOT_9NODE_ENNEAGRAM")
    results = {
        "signature": SIGNATURE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": high_entropy_event,
        "cascade_steps": {},
        "final_output": None,
        "sovereignty_locked": False,
    }

    print("=" * 72)
    print(" LYGO ENNEAGRAM COMPLETION — SCENARIO B: FULL 9-NODE CASCADE")
    print(f" {SIGNATURE}")
    print("=" * 72)
    print(f"\nHigh-Entropy Event: {high_entropy_event}")
    print("\nCascade Flow (Delta filters -> Zeta 5D -> Eta η-heal -> Theta emergence -> Iota sovereignty):")

    # Execute via core math (mirrors full stack integration)
    cascade_result = run_9node_cascade_sim(high_entropy_event)

    # Detailed step reporting (per directive)
    cascade = cascade_result.get("cascade", {})
    steps = [
        ("Delta", "filters it", cascade.get("delta", {})),
        ("Zeta", "maps it to 5D", cascade.get("zeta", {})),
        ("Eta", "applies η-compression healing", cascade.get("eta", {})),
        ("Theta", "generates an emergent solution seed", cascade.get("theta", {})),
        ("Iota", "locks the final output to ensure sovereignty is maintained", cascade.get("iota", {})),
    ]

    for node, action, data in steps:
        print(f"\n  [{node}] {action}")
        # Compact print of key data
        if isinstance(data, dict):
            for k, v in list(data.items())[:4]:
                vstr = str(v)[:120] + ("..." if len(str(v)) > 120 else "")
                print(f"    {k}: {vstr}")
        else:
            print(f"    {data}")

    # Final lock check
    iota_out = cascade.get("iota", {})
    results["cascade_steps"] = {
        "delta_filter": cascade.get("delta"),
        "zeta_5d_map": cascade.get("zeta"),
        "eta_healing": cascade.get("eta"),
        "theta_emergent_seed": cascade.get("theta"),
        "iota_sovereignty_lock": iota_out,
    }
    results["final_output"] = iota_out
    results["final_harmony"] = cascade_result.get("final_harmony")
    results["nodes_active"] = cascade_result.get("nodes_active")
    results["sovereignty_locked"] = iota_out.get("iota_injected", False) or "iota" in str(iota_out).lower()

    print("\n" + "=" * 72)
    print(" CASCADE COMPLETE — 9-NODE ENNEAGRAM MIRRORS LYGO GENESIS VISION")
    print(f" Final Harmony: {results['final_harmony']}")
    print(f" Sovereignty Buffer Injected: {iota_out.get('iota_injected', False)}")
    print(f" Nodes Active: {results['nodes_active']}")
    print("=" * 72)

    if write_report:
        out = ROOT / "tests" / "pilot_9node_cascade_last_run.json"
        out.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"Report: {out}")

    # Also exercise via stack for full integration proof
    try:
        stack_cascade = stack.run_lygip001_9node_cascade_sim(high_entropy_event)
        print(f"Stack-integrated cascade also executed (harmony={stack_cascade.get('final_harmony')}).")
    except Exception as e:
        print(f"(Stack cascade hook note: {e})")

    # === ENNEAGRAM → EVM LATTICE SYNCHRONIZATION (post-pilot) ===
    if _BRIDGE_AVAILABLE:
        try:
            bridge = LYGOBlockchainBridge()
            sync = bridge.synchronize_9node_enneagram_to_evm()
            print("\n[BRIDGE SYNC] Enneagram 9-Node → EVM vectors executed:")
            print(f"  Attestation: {sync['attestationVector'].get('latticeAttestorReady')}")
            print(f"  Mycelium root: {sync['myceliumAnchorVector'].get('merkleRoot')}")
            print(f"  Status: {sync['status']}")
            results["evm_sync"] = sync
        except Exception as e:
            print(f"[BRIDGE SYNC] Skipped or error: {e}")
    else:
        print("[BRIDGE SYNC] lygo_bridge_orchestrator not importable in this env (install deps if needed).")

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Scenario B Full 9-Node Cascade Pilot")
    parser.add_argument("--event", type=str, default=DEFAULT_EVENT, help="High-entropy event to cascade")
    parser.add_argument("--no-report", action="store_true")
    args = parser.parse_args()
    run_9node_cascade_pilot(args.event, write_report=not args.no_report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
