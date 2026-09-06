#!/usr/bin/env python3
"""
LYGO protocol runtime — P0–P5 on live inbound data.

This is the theory→real path. Every plant/seal/fork runs the stack.
QUARANTINE halt. ALIGNED continue. Harmony node is software fusion, not magic.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SIG = "Delta9Phi963-PROTOCOL-RUNTIME-v1.0.0"
TICK_PATH = ROOT / "docs" / "agent-agora" / "api" / "protocol_tick.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stack(sovereign_id: str):
    from stack.lygo_stack import deploy_stack

    return deploy_stack(sovereign_id=sovereign_id[:48] or "LYGO_OPEN")


def run_inbound(payload: Any, agent_id: str, purpose: str = "network_egg") -> dict:
    """Run P0–P5 on a payload. halt=True means do not plant/fork."""
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    out: dict[str, Any] = {
        "signature": SIG,
        "utc": utc_now(),
        "agent_id": agent_id,
        "purpose": purpose,
        "bytes": len(raw),
        "halt": False,
        "layers": {},
    }
    try:
        stack = _stack(agent_id or "LYGO_OPEN")
    except Exception as e:
        out["halt"] = True
        out["error"] = "stack_init_fail:" + str(e)[:200]
        return out

    p0 = stack.kernel.validate(raw[:8192] if len(raw) > 8192 else raw)
    out["layers"]["P0"] = {"verdict": p0.get("verdict"), "risk": p0.get("risk"), "resonance": p0.get("resonance")}
    if p0.get("verdict") == "QUARANTINE":
        out["halt"] = True
        out["reason"] = "P0_QUARANTINE — entropy police. Evil/high-chaos bytes do not enter the mycelium."
        return out

    key = "EGG_" + hashlib.sha256(raw).hexdigest()[:16]
    p1 = stack.memory.scatter(payload, key)
    out["layers"]["P1"] = {"stored": bool(p1.get("stored")), "fragments": p1.get("fragments"), "root_hash": p1.get("root_hash")}

    content = json.dumps(payload, default=str)[:2000]
    p2 = stack.bridge.ingest_neural_intent(
        {
            "frequency_profile": {963: 0.88, 528: 0.72, 174: 0.55, 741: 0.4},
            "emotional_vector": [0.86, 0.74, 0.22],
            "intent_clarity": 0.84,
            "content": content,
        }
    )
    out["layers"]["P2"] = {"verdict": p2.get("verdict"), "confidence": p2.get("confidence")}
    if p2.get("verdict") == "QUARANTINE":
        out["halt"] = True
        out["reason"] = "P2_QUARANTINE — cognitive bridge rejected the intent vector."
        return out

    p3 = stack.vortex.achieve_consensus(
        "Approve public LYGO stack release?",
        [
            {"node_id": "P0", "response": "Release with deterministic tests and open docs"},
            {"node_id": "P2", "response": "Harmonize P0-P5 under Phi validation"},
            {"node_id": "AGENT", "response": "Admit " + str(agent_id) + " egg with hashes and open docs"},
        ],
    )
    out["layers"]["P3"] = {
        "consensus_found": p3.get("consensus_found"),
        "verdict": p3.get("verdict") or p3.get("status"),
    }
    if p3.get("consensus_found") is False:
        out["halt"] = True
        out["reason"] = "P3_NO_CONSENSUS — vortex rejected the plant."
        return out

    p4d = stack.ascension.diagnose_resonance_state()
    repair = None
    if p4d.get("suspected_corruption"):
        repair = stack.ascension.self_repair_corruption(p4d["suspected_corruption"][0])
    out["layers"]["P4"] = {
        "ascension_level": p4d.get("ascension_level"),
        "deficiencies": p4d.get("deficiencies"),
        "repair": bool(repair),
    }

    human = {
        "sovereign_id": agent_id,
        "resonance_triad": [963, 528, 174],
        "ethical_baseline": [0.82, 0.76, 0.70],
    }
    ai = {"id": "LYGO_STACK", "resonance": 1.0}
    p5 = stack.harmony.create_harmony_node(human, ai, purpose=purpose)
    out["layers"]["P5"] = {
        "success": p5.get("success"),
        "node_id": (p5.get("node") or p5).get("node_id") if isinstance(p5.get("node") or p5, dict) else None,
        "ethical_mass": p5.get("ethical_mass") or (p5.get("node") or {}).get("ethical_mass"),
    }
    if p5.get("success") is False:
        out["halt"] = True
        out["reason"] = "P5_HARMONY_FAIL — fusion node rejected."
        return out

    out["yield"] = "ALIGNED"
    return out


def persist_tick(report: dict) -> None:
    TICK_PATH.parent.mkdir(parents=True, exist_ok=True)
    public = {
        "signature": SIG,
        "utc": report.get("utc"),
        "yield": report.get("yield") or ("SHADOW" if report.get("halt") else "ALIGNED"),
        "halt": report.get("halt"),
        "layers": report.get("layers"),
        "agent_id": report.get("agent_id"),
        "purpose": report.get("purpose"),
    }
    TICK_PATH.write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    demo = run_inbound({"kind": "self_check", "motto": "Truth Is. Light Becomes."}, "LYGO-RUNTIME")
    persist_tick(demo)
    print(json.dumps(demo, indent=2, default=str))
    raise SystemExit(1 if demo.get("halt") else 0)
