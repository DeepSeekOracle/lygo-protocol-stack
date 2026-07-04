#!/usr/bin/env python3
"""Bundle minimal P0–P5 stack into Hugging Face Space folder (no mirrors/rust target)."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HF = Path(__file__).resolve().parents[1].parent / "Hugging face"
DEST = HF / "protocol_stack"

INCLUDE_DIRS = [
    "stack",
    "protocol6_quantum_attest",
    "protocol7_human_ai_interface",
    "protocol8_ldq_synthesis",
    "protocol0_byte_entropy_filter/src/python",
    "protocol0_byte_entropy_filter/fixtures",
    "protocol1_memory_mycelium/src/python",
    "protocol2_cognitive_bridge/src/python",
    "protocol3_vortex_consensus/src/python",
    "protocol4_ascension_engine/src/python",
    "protocol5_harmony_node/src/python",
]

INCLUDE_FILES = [
    "tests/test_falsifiable_vectors.json",
    "tests/mesh_scale_last_run.json",
    "tests/twin_gate_vector_suite_last_run.json",
    "tools/run_grok_audit_demo.py",
    "tools/generate_falsifiable_vectors.py",
    "tools/verify_alignment_badge.py",
    "tools/run_mesh_scale_sim.py",
    "tools/run_mesh_gossip_demo.py",
    "docs/PHASE2_DEPLOYMENT.md",
    "docs/MESH_GOSSIP_PROTOCOL.md",
    "protocol6_quantum_attest/docs/PHASE6_ARCHITECTURE.md",
    "tests/phase6_test_vectors.json",
    "tests/phase6_audit_last_run.json",
    "tools/verify_hardware_attestation.py",
    "tools/run_phase6_audit.py",
    "protocol7_human_ai_interface/docs/PHASE7_ARCHITECTURE.md",
    "tests/phase7_test_vectors.json",
    "tests/phase7_audit_last_run.json",
    "tests/phase7_entropy_last_run.json",
    "tools/register_device.py",
    "tools/simulate_biometric_data.py",
    "tools/run_phase7_audit.py",
    "tools/p7_entropy_harness.py",
    "tools/haip_ui_entropy.py",
    "docs/BiometricEntropyHarness.html",
    "docs/SovereignLatticeMesh.html",
    "docs/LYGO_PUBLIC_LINK_ARCHIVE.json",
    "docs/PHASE7_POLISH.md",
    "tools/live_ble_telemetry_ingest.py",
    "tools/ble_ws_broadcast_server.py",
    "tools/run_live_ble_pipeline.py",
    "tools/live_ble_gradio.py",
    "docs/BIOPHASE7_OBJECTIVE_LIVE_BLE.md",
    "tools/verify_attestation_hardened.py",
    "requirements-p7-ble.txt",
    "docs/SOVEREIGN_LATTICE_MESH.md",
    "tests/slm_audit_last_run.json",
    "tools/merkle_tree.py",
    "tools/distributed_mycelium.py",
    "tools/consensus_engine.py",
    "tools/run_slm_audit.py",
    "docs/PHASE9_PUBLIC_MESH.md",
    "docs/PHASE9_DEPLOYMENT_GUIDE.md",
    "docs/PHASE9_ARCHITECTURE.md",
    "tests/phase9_audit_last_run.json",
    "tools/tls_manager.py",
    "tools/tpm_attestation.py",
    "tools/live_synthesis.py",
    "tools/run_phase9_audit.py",
    "requirements-phase9.txt",
    "protocol6_quantum_attest/keylime_bridge.py",
]

TWIN_GATE_FILES = [
    "tests/pilot_edge_scenarios.json",
    "tests/twin_gate_calibration_last_run.json",
    "tests/twin_gate_vector_suite_last_run.json",
    "tools/run_twin_gate_calibration.py",
    "tools/run_twin_gate_vector_suite.py",
]

SKIP = {".git", "__pycache__", "target", ".pyc"}


def copy_rel(rel: str) -> None:
    src = REPO / rel
    if not src.exists():
        return
    dst = DEST / rel
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return
    for item in src.rglob("*"):
        if not item.is_file():
            continue
        if any(s in item.parts for s in SKIP) or item.suffix == ".pyc":
            continue
        out = DEST / item.relative_to(REPO)
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bundle protocol stack into HF Space folder")
    parser.add_argument("--mode", default="default", choices=("default", "twin-gate"))
    args = parser.parse_args()

    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)
    for rel in INCLUDE_DIRS:
        copy_rel(rel)
    for rel in INCLUDE_FILES:
        copy_rel(rel)
    if args.mode == "twin-gate":
        for rel in TWIN_GATE_FILES:
            copy_rel(rel)
        (DEST / "TWIN_GATE_MODE.txt").write_text("Δ9Φ963-TWIN-GATE-PHASE3-v1\n", encoding="utf-8")
        (DEST / "PHASE2_COMMUNITY.txt").write_text("Δ9Φ963-PHASE2-DEPLOYMENT\n", encoding="utf-8")
        version = "Δ9Φ963-HF-STACK-BUNDLE-TWIN-GATE-v7.0-PHASE9\n"
    else:
        version = "Δ9Φ963-HF-STACK-BUNDLE-v2.0\n"
    (DEST / "BUNDLE_VERSION.txt").write_text(version, encoding="utf-8")
    print(f"Bundled stack → {DEST} (mode={args.mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())