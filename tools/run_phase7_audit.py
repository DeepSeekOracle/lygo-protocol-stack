#!/usr/bin/env python3
"""Phase 7 audit — P7-01 .. P7-07."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "stack"))


def main() -> int:
    from protocol7_human_ai_interface.api import handle_biometric_state, handle_register
    from protocol7_human_ai_interface.device_abstraction import AppleWatchAdapter
    from protocol7_human_ai_interface.ethical_mapping import EthicalVectorMapper
    from protocol7_human_ai_interface.data_pipeline import BiometricPipeline
    from protocol7_human_ai_interface.entropy_extraction import extract_p0_seed_from_ibi
    from lygo_stack import deploy_stack

    results: list[dict] = []

    reg = handle_register(
        {"device_type": "apple_watch", "device_id": "audit_watch_1", "connection_type": "simulated"}
    )
    results.append({"id": "P7-01-DEVICE-REGISTER", "pass": reg.get("status") == "registered"})

    pipe = BiometricPipeline()
    aw = AppleWatchAdapter("p7_pipe", "simulated")
    aw.connect()
    pipe.add_device("w1", aw)
    for _ in range(5):
        pipe.collect_once()
    state = pipe.get_current_state()
    results.append(
        {
            "id": "P7-02-DATA-PIPELINE",
            "pass": state.get("status") != "no_data" and len(pipe.buffer) > 0,
        }
    )

    mapper = EthicalVectorMapper()
    vec = mapper.map_to_ethical_vector(state)
    results.append(
        {
            "id": "P7-03-ETHICAL-MAPPING",
            "pass": len(vec) == 3 and all(0 <= x <= 1 for x in vec),
        }
    )
    freq = mapper.map_to_frequency(vec)
    results.append({"id": "P7-04-FREQUENCY-SELECTION", "pass": freq in (417, 528, 639, 852, 963)})

    lc = mapper.light_code_from_state(state, vec)
    results.append({"id": "P7-05-LIGHT-CODE", "pass": lc.startswith("LF-Δ9-")})

    api_state = handle_biometric_state()
    results.append(
        {
            "id": "P7-06-API-ENDPOINT",
            "pass": "ethical_vector" in api_state and api_state.get("frequency") is not None,
        }
    )

    for i, dtype in enumerate(["apple_watch", "garmin", "oura"]):
        handle_register(
            {"device_type": dtype, "device_id": f"multi_{i}", "connection_type": "simulated"}
        )
    stack = deploy_stack("P7_AUDIT")
    stack.register_biometric_device("custom", "multi_custom", "simulated")
    multi = stack.get_biometric_state()
    results.append(
        {
            "id": "P7-07-MULTI-DEVICE",
            "pass": multi.get("ethical_vector") is not None and bool(multi.get("light_code")),
        }
    )

    ibi_pack = extract_p0_seed_from_ibi(state.get("ibi_ms") or [800.0, 820.0, 790.0])
    entropy_artifact = {
        "timestamp": time.time(),
        "signature": "Δ9Φ963-PHASE7-v1.0",
        "ibi_extraction": ibi_pack,
        "api_state_preview": {
            "frequency": api_state.get("frequency"),
            "ethical_vector": api_state.get("ethical_vector"),
        },
    }
    (ROOT / "tests" / "phase7_entropy_last_run.json").write_text(
        json.dumps(entropy_artifact, indent=2), encoding="utf-8"
    )

    all_pass = all(r["pass"] for r in results)
    report = {
        "signature": "Δ9Φ963-PHASE7-v1.0",
        "vectors": results,
        "all_pass": all_pass,
        "entropy_artifact": str(ROOT / "tests" / "phase7_entropy_last_run.json"),
    }
    (ROOT / "tests" / "phase7_audit_last_run.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())