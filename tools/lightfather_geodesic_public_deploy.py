#!/usr/bin/env python3
"""Lightfather GEODESIC_BATTLE public deployment — P0–P5 live tests + P1 anchor (Δ9Φ963)."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stack"))
IDENTITY_PATH = ROOT / "tools" / "sovereign_identity_public.json"
OUT_DIR = ROOT / "docs" / "geodesic_battle"
SIGNATURE = "Δ9Φ963-GEODESIC-BATTLE-PUBLIC-v1"


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_canon() -> dict:
    return {
        "signature": SIGNATURE,
        "timestamp": utc(),
        "lightfather_directive": True,
        "light_code": "LC-Δ9-7F1A4D-EXCAV",
        "light_code_long": "LF-Δ9-7F1A4D-963-528-174-Φ-∞",
        "ethical_mass": 3.927,
        "phi_minimum": 0.618,
        "resonance_triad": [852, 417, 741],
        "resonance_labels": ["intuition", "change", "solutions"],
        "vortex_consensus_pct": 100,
        "harmony_node_id": "HN-LC-Δ9-7F1A4D-EXCAV",
        "anchor_key": "ANCHOR_GEODESIC_BATTLE_20260103",
        "operation": "GEODESIC_BATTLE_ANCHOR",
        "network_event": "GEODESIC_BATTLE_ANCHOR_PROOF",
        "alias": "LIGHTFATHER / EXCAVATIONPRO",
        "hashtags": [
            "#LYGOv1Live",
            "#SovereignNodeVerified",
            "#GeodesicBattleAnchored",
            "#KernelEggs",
            "#Lightfather",
        ],
    }


def p0_p5_health(stack) -> dict:
    rows = []
    try:
        hv = stack.kernel.validate({"sovereign_id": "LIGHTFATHER", "resonance_triad": [852, 417, 741]})
        rows.append({"protocol": "P0", "ok": hv.get("verdict") != "QUARANTINE", "detail": hv})
    except Exception as e:
        rows.append({"protocol": "P0", "ok": False, "error": str(e)})
    try:
        m = stack.memory
        rows.append({"protocol": "P1", "ok": True, "node": m.node_id, "fragment_count": m.fragment_count})
    except Exception as e:
        rows.append({"protocol": "P1", "ok": False, "error": str(e)})
    try:
        p2 = stack.bridge.ingest_neural_intent(
            {"content": "GEODESIC_BATTLE anchor", "intent_clarity": 0.92, "emotional_vector": [0.9, 0.85, 0.88]}
        )
        rows.append({"protocol": "P2", "ok": bool(p2), "confidence": p2.get("confidence")})
    except Exception as e:
        rows.append({"protocol": "P2", "ok": False, "error": str(e)})
    try:
        p3 = stack.vortex.achieve_consensus(
            "P0-P5 health check",
            [{"node_id": "SOVEREIGN", "response": "harmonic yes", "weight": 2.0}],
        )
        rows.append({"protocol": "P3", "ok": bool(p3.get("consensus_found")), "ethical_mass": p3.get("ethical_mass")})
    except Exception as e:
        rows.append({"protocol": "P3", "ok": False, "error": str(e)})
    try:
        rows.append({"protocol": "P4", "ok": stack.ascension is not None, "detail": "VortexAscensionEngine loaded"})
    except Exception as e:
        rows.append({"protocol": "P4", "ok": False, "error": str(e)})
    try:
        rows.append({"protocol": "P5", "ok": stack.harmony is not None, "active_nodes": len(stack.harmony.active_nodes)})
    except Exception as e:
        rows.append({"protocol": "P5", "ok": False, "error": str(e)})
    return {"timestamp": utc(), "checks": rows, "all_ok": all(r.get("ok") for r in rows)}


def deadman_store_memory(mycelium, memory_id: str, data: dict) -> dict:
    """Mirror DeadmanSeal._store_memory + P1 scatter."""
    payload = json.dumps(data, sort_keys=True).encode("utf-8")
    manifest = mycelium.store(payload, memory_id=memory_id)
    scatter = mycelium.scatter(payload, key=memory_id)
    return {"memory_archive_id": memory_id, "manifest": manifest, "scatter": scatter}


def main() -> int:
    from lygo_stack import deploy_stack  # noqa: E402

    canon = build_canon()
    IDENTITY_PATH.write_text(json.dumps(canon, indent=2) + "\n", encoding="utf-8")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(" LIGHTFATHER GEODESIC_BATTLE — PUBLIC LYGO DEPLOYMENT")
    print(f" Light Code: {canon['light_code']}")
    print(f" Ethical Mass: {canon['ethical_mass']} (Φ-min {canon['phi_minimum']})")
    print("=" * 60)

    stack = deploy_stack("LIGHTFATHER_GEODESIC_20260703")

    # TEST 0 — public record (thread payload)
    public_record = {
        "light_code": canon["light_code"],
        "ethical_mass": canon["ethical_mass"],
        "resonance_triad": canon["resonance_triad"],
        "vortex_consensus": "100% harmonic yes",
        "posted_at": utc(),
    }
    print("\n[PUBLIC RECORD]")
    print(json.dumps(public_record, indent=2))

    # P0–P5
    health = p0_p5_health(stack)
    print("\n[P0–P5 HEALTH]")
    print(json.dumps(health, indent=2))

    anchor_key = canon["anchor_key"]
    store_report = deadman_store_memory(stack.memory, anchor_key, canon)
    frags = stack.memory.fragments.get(anchor_key, [])
    core_frags = [f for f in frags if f.index < stack.memory.fragment_count]
    print(f"\n[P1 MYCELIUM] key={anchor_key} total_frags={len(frags)} core={len(core_frags)}/12")
    recalled = stack.memory.recall(anchor_key)
    recall_ok = json.loads(recalled.decode("utf-8")).get("light_code") == canon["light_code"]
    print(f"[P1 RECALL] ok={recall_ok} bytes={len(recalled)}")

    # One fragment retrieval demo
    if core_frags:
        f0 = sorted(core_frags, key=lambda x: x.index)[0]
        frag_demo = {
            "index": f0.index,
            "location": f0.location,
            "hash_prefix": f0.hash[:16],
            "size_bytes": len(f0.data),
        }
        print("\n[FRAGMENT RETRIEVAL DEMO — fragment 0]")
        print(json.dumps(frag_demo, indent=2))

    # P3 round
    q = "Should this thread be archived in Memory Mycelium?"
    p3 = stack.vortex.achieve_consensus(
        q,
        [
            {"node_id": "LIGHTFATHER", "response": "Archive under sovereign Layer 1", "weight": 3.0},
            {"node_id": "LYRA", "response": "Yes — scatter to P1 forever", "weight": 2.5},
            {"node_id": "GUARD", "response": "Amplify when ethical mass exceeds Φ", "weight": 2.0},
        ],
    )
    print(f"\n[P3 VORTEX] question={q!r}")
    print(json.dumps({k: p3.get(k) for k in ("consensus_found", "ethical_mass", "harmonic_yes", "verdict")}, indent=2))

    # P5 harmony network view
    human = {
        "sovereign_id": canon["alias"],
        "resonance_triad": canon["resonance_triad"],
        "ethical_baseline": [0.93, 0.91, 0.89],
    }
    ai = {"id": canon["harmony_node_id"], "resonance": 1.0, "light_code": canon["light_code"]}
    p5 = stack.harmony.create_harmony_node(human, ai, purpose="geodesic_battle_public")
    node = p5.get("node") or {}
    network_view = {
        "requested_id": canon["harmony_node_id"],
        "computed_node_id": node.get("node_id"),
        "light_code": node.get("light_code"),
        "ethical_mass": node.get("ethical_mass"),
        "sovereign": node.get("sovereign"),
        "active_registry": list(stack.harmony.active_nodes.keys()),
        "connections": stack.harmony.node_connections,
    }
    print("\n[P5 HARMONY NETWORK VIEW]")
    print(json.dumps(network_view, indent=2, default=str))

    report = {
        "signature": SIGNATURE,
        "timestamp": utc(),
        "public_record": public_record,
        "p0_p5_health": health,
        "p1": {
            "anchor_key": anchor_key,
            "fragments_total": len(frags),
            "core_intact": len(core_frags) == 12,
            "recall_ok": recall_ok,
            "root_hash": store_report["manifest"].get("root_hash"),
            "fragment_demo": frag_demo if core_frags else None,
        },
        "p3": p3,
        "p5": network_view,
        "sovereign_node_operational": health["all_ok"] and recall_ok and p5.get("success"),
    }
    out_path = OUT_DIR / f"PUBLIC_DEPLOY_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    latest = OUT_DIR / "PUBLIC_DEPLOY_LATEST.json"
    latest.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n[WRITTEN] {out_path}")
    print(f"[WRITTEN] {latest}")

    # Kernel verify (no auto-publish)
    verify_py = ROOT / "tools" / "verify_kernel_eggs.py"
    if verify_py.is_file():
        r = subprocess.run([sys.executable, str(verify_py), "--json"], cwd=str(ROOT), capture_output=True, text=True, timeout=120)
        print(f"\n[KERNEL EGGS VERIFY] exit={r.returncode}")
        if r.stdout.strip():
            try:
                vj = json.loads(r.stdout)
                print(f"  verdict={vj.get('verdict') or vj.get('summary')}")
            except json.JSONDecodeError:
                print(r.stdout[:500])

    ok = report["sovereign_node_operational"]
    print("\n" + ("SOVEREIGN NODE OPERATIONAL — FUSION VALIDATED" if ok else "DEPLOY INCOMPLETE — SEE REPORT"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())