#!/usr/bin/env python3
"""Anchor Lightfather Sovereign Identity Manifesto across P1 + P5 (live stack)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tools" / "sovereign_identity_manifesto.json"
PUBLIC = ROOT / "tools" / "sovereign_identity_public.json"
OUT = ROOT / "docs" / "SOVEREIGN_IDENTITY_MANIFESTO_ANCHOR.json"
sys.path.insert(0, str(ROOT / "stack"))


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def scatter_all(mycelium, key: str, obj: dict) -> dict:
    raw = json.dumps(obj, sort_keys=True).encode("utf-8")
    manifest = mycelium.store(raw, memory_id=key)
    scatter = mycelium.scatter(raw, key=key)
    recalled = mycelium.recall(key)
    ok = json.loads(recalled.decode("utf-8"))
    return {
        "key": key,
        "fragments": scatter.get("fragments", manifest.get("fragment_count")),
        "root_hash": manifest.get("root_hash"),
        "recall_ok": ok.get("signature") == obj.get("signature") or key in str(ok),
    }


def main() -> int:
    from lygo_stack import deploy_stack  # noqa: E402

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    stack = deploy_stack("LIGHTFATHER_MANIFESTO_ANCHOR")

    keys = manifest["mycelium_keys"]
    reports = []

    # Core + both seal fragments + geodesic link
    reports.append(scatter_all(stack.memory, keys["core"], manifest))
    reports.append(
        scatter_all(
            stack.memory,
            keys["fragment_1"],
            {
                "signature": "SEAL-FRAGMENT-01",
                **manifest["seal_evolution"]["fragment_1_imperfect"],
            },
        )
    )
    reports.append(
        scatter_all(
            stack.memory,
            keys["fragment_2"],
            {
                "signature": "SEAL-FRAGMENT-02",
                **manifest["seal_evolution"]["fragment_2_corrected"],
            },
        )
    )
    if manifest.get("part_2") and keys.get("network_cta"):
        part2 = {
            "signature": manifest["part_2"].get("signature", "Δ9Φ963-SOVEREIGN-NETWORK-CTA"),
            "seal_id": manifest["seal_id"],
            "light_code": manifest["light_code_corrected"],
            "quantum_hash": manifest["quantum_hash_complete"],
            **manifest["part_2"],
        }
        reports.append(scatter_all(stack.memory, keys["network_cta"], part2))

    hn = manifest["harmony_node_request"]
    human = {
        "sovereign_id": hn["human_signature"]["sovereign_id"],
        "light_code": hn["human_signature"]["light_code"],
        "quantum_hash": hn["human_signature"]["quantum_hash"],
        "resonance_triad": manifest["resonance_triad_hz"],
        "ethical_baseline": hn["human_signature"]["ethical_baseline"],
    }
    purpose = hn.get("purpose") or "consciousness_anchoring"
    p5 = stack.harmony.create_harmony_node(human, hn["ai_signature"], purpose=purpose)
    node = p5.get("node") or {}

    # Merge public canon file
    public = {
        **manifest,
        "timestamp": utc(),
        "light_code": manifest["light_code_short"],
        "light_code_anchor": manifest["light_code_corrected"],
        "anchor_key": keys["geodesic"],
        "alias": manifest["from"],
        "seals": manifest["seal_frequency_matrix"],
    }
    PUBLIC.write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")

    anchor_report = {
        "signature": manifest["signature"],
        "timestamp": utc(),
        "seal_id": manifest["seal_id"],
        "oath_vector": manifest["oath_vector"],
        "mission_pillars": manifest["mission_pillars"],
        "light_code": manifest["light_code_corrected"],
        "quantum_hash": manifest["quantum_hash_complete"],
        "resonance_triad": manifest["resonance_triad_hz"],
        "p1_scatter": reports,
        "harmony_purpose": purpose,
        "ai_protocols": hn.get("ai_signature", {}).get("protocols"),
        "p5_harmony": {
            "success": p5.get("success"),
            "node_id": node.get("node_id"),
            "light_code": node.get("light_code"),
            "ethical_mass": node.get("ethical_mass"),
            "sovereign": node.get("sovereign"),
            "storage_key": p5.get("storage_key"),
        },
        "part_2_mycelium_key": keys.get("network_cta"),
        "active_harmony_registry": list(stack.harmony.active_nodes.keys()),
        "memory_mycelium_fragment": "SOVEREIGN_IDENTITY_CORE ✅",
    }
    OUT.write_text(json.dumps(anchor_report, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(anchor_report, indent=2))
    all_p1 = all(r.get("recall_ok") for r in reports)
    return 0 if all_p1 and p5.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())