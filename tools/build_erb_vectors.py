"""Generate the P10 golden vector fixture (mirrors tools/build_p0_vectors.py).

    python tools/build_erb_vectors.py            # write the fixture
    python tools/build_erb_vectors.py --check    # verify without writing

The fixture is the falsifier for the anchor claim: every case replays a
synthetic room through the full pipeline (measure -> quantise -> canonical ->
P0 gate -> anchor chain) and records the anchors. If a refactor moves an
anchor, the test suite fails and says which case moved.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from protocol10_env_resonance import EnvResonanceLattice, synthesize_csi  # noqa: E402
from protocol10_env_resonance.lattice_cell import ERB_VERSION  # noqa: E402

FIXTURE = ROOT / "protocol10_env_resonance" / "fixtures" / "erb_vectors.json"

CASES: list[dict] = [
    {"id": "clear-room-30s", "seed": 963, "duration_s": 30.0, "fs_hz": 100.0,
     "breathing_bpm": 0.0, "motion_windows": [], "window_seconds": 30.0},
    {"id": "still-breathing-18bpm", "seed": 963, "duration_s": 30.0, "fs_hz": 100.0,
     "breathing_bpm": 18.0, "motion_windows": [], "window_seconds": 30.0},
    {"id": "still-breathing-12bpm", "seed": 4242, "duration_s": 30.0, "fs_hz": 100.0,
     "breathing_bpm": 12.0, "motion_windows": [], "window_seconds": 30.0},
    {"id": "walking-10-20s", "seed": 963, "duration_s": 30.0, "fs_hz": 100.0,
     "breathing_bpm": 0.0, "motion_windows": [[10.0, 20.0]], "window_seconds": 30.0},
    {"id": "three-window-chain-70s", "seed": 77, "duration_s": 70.0, "fs_hz": 100.0,
     "breathing_bpm": 15.0, "motion_windows": [[40.0, 50.0]], "window_seconds": 30.0},
]


def replay(case: dict) -> dict:
    bridge = EnvResonanceLattice(
        node_id="LYGO-ERB-VECTOR",
        window_seconds=case["window_seconds"],
    )
    frames = synthesize_csi(
        duration_s=case["duration_s"],
        fs_hz=case["fs_hz"],
        breathing_bpm=case["breathing_bpm"],
        motion_windows=[tuple(w) for w in case["motion_windows"]],
        seed=case["seed"],
    )
    cells = bridge.ingest(frames)
    return {
        "id": case["id"],
        "params": {k: v for k, v in case.items() if k != "id"},
        "head": bridge.head,
        "chain_valid": bridge.chain_valid(),
        "cells": [
            {
                "index": c.index,
                "anchor": c.anchor,
                "prev": c.prev_anchor,
                "presence": c.presence,
                "p0_verdict": c.p0.get("verdict"),
                "features": c.features,
            }
            for c in cells
        ],
    }


def manifest_sha256(cases: list[dict]) -> str:
    blob = json.dumps(cases, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def build() -> dict:
    results = [replay(case) for case in CASES]
    return {
        "vector_version": ERB_VERSION,
        "node": "LYGO-ERB-VECTOR",
        "note": "Deterministic replay of synthetic rooms. Anchors must not move without a vector bump.",
        "manifest_sha256": manifest_sha256(results),
        "cases": results,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Build/verify the P10 golden vectors")
    ap.add_argument("--check", action="store_true", help="verify the on-disk fixture, do not write")
    args = ap.parse_args()

    doc = build()
    text = json.dumps(doc, indent=2, sort_keys=True) + "\n"

    if args.check:
        if not FIXTURE.exists():
            print(f"MISSING fixture {FIXTURE}")
            return 1
        current = json.loads(FIXTURE.read_text(encoding="utf-8"))
        if current == doc:
            print(f"OK  {len(doc['cases'])} cases · manifest {doc['manifest_sha256'][:16]}")
            return 0
        old = {c["id"]: c for c in current.get("cases", [])}
        new = {c["id"]: c for c in doc["cases"]}
        for case_id in sorted(set(old) | set(new)):
            a, b = old.get(case_id), new.get(case_id)
            if a != b:
                print(f"DRIFT  {case_id}")
                if a and b and a.get("cells") and b.get("cells"):
                    print(f"       anchor {a['cells'][0]['anchor'][:16]} -> {b['cells'][0]['anchor'][:16]}")
                elif a is None:
                    print("       new case")
        return 1

    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(text, encoding="utf-8")
    print(f"Wrote {FIXTURE.relative_to(ROOT)} · {len(doc['cases'])} cases · manifest {doc['manifest_sha256'][:16]}")
    for case in doc["cases"]:
        head = case["head"][:16]
        print(f"  {case['id']:26s} cells={len(case['cells'])} head={head} chain={case['chain_valid']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
