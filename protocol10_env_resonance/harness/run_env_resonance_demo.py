"""P10 harness — run the Environmental Resonance Bridge end to end.

    python protocol10_env_resonance/harness/run_env_resonance_demo.py           # human report
    python protocol10_env_resonance/harness/run_env_resonance_demo.py --json    # machine report

Four synthetic rooms are replayed through the full pipeline: CSI physics ->
fixed-point quantisation -> canonical bytes -> P0 gate -> chained SHA-256
anchor -> P1 memory scatter + recall -> P8 harmonic hand-off.

Every number printed here is measured in this run. Nothing is hardcoded.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_ROOT = _HERE.parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from protocol10_env_resonance import EnvResonanceLattice, synthesize_csi  # noqa: E402
from protocol10_env_resonance.bridge import P0_AVAILABLE, P1_AVAILABLE, P8_AVAILABLE  # noqa: E402

ROOMS = [
    ("clear room, 30 s", dict(breathing_bpm=0.0, motion_windows=[])),
    ("still person breathing 18 bpm", dict(breathing_bpm=18.0, motion_windows=[])),
    ("still person breathing 12 bpm", dict(breathing_bpm=12.0, motion_windows=[])),
    ("someone walking 10-20 s", dict(breathing_bpm=0.0, motion_windows=[(10.0, 20.0)])),
]


def run() -> dict:
    out: dict = {"rooms": [], "integration": {
        "p0_gate": P0_AVAILABLE,
        "p1_memory": P1_AVAILABLE,
        "p8_resonance": P8_AVAILABLE,
    }}
    for label, params in ROOMS:
        bridge = EnvResonanceLattice(node_id="LYGO-ERB-DEMO")
        frames = synthesize_csi(duration_s=30.0, fs_hz=100.0, seed=963, **params)
        cells = bridge.ingest(frames)
        cell = cells[0]
        recalled = None
        if P1_AVAILABLE:
            recalled = bridge.recall(0).decode("utf-8")
        out["rooms"].append(
            {
                "room": label,
                "cells": len(cells),
                "presence": cell.presence,
                "admitted": cell.admitted,
                "motion_cdb": cell.features["motion_cdb"],
                "breath_energy_cdb": cell.features["breath_energy_cdb"],
                "breath_rate_bpm": cell.features["breath_rate_mbpm"] / 1000.0,
                "breath_snr_db": cell.features["breath_snr_cdb"] / 100.0,
                "p0_verdict": cell.p0.get("verdict"),
                "anchor": cell.anchor,
                "prev_anchor": cell.prev_anchor,
                "resonance": cell.resonance,
                "memory_root": cell.memory.get("root_hash"),
                "recalled_matches": recalled is not None
                and json.loads(recalled)["anchor"] == cell.anchor,
            }
        )
        out["rooms"][-1]["report"] = bridge.report()
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="P10 Environmental Resonance Bridge demo")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON only")
    args = ap.parse_args()

    result = run()

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print("LYGO P10 - Environmental Resonance Bridge")
    print("=" * 78)
    print("integration:  P0 gate=%s  P1 memory=%s  P8 resonance=%s" % (
        result["integration"]["p0_gate"],
        result["integration"]["p1_memory"],
        result["integration"]["p8_resonance"],
    ))
    print()
    header = f"{'room':32s} {'state':8s} {'motion':>9s} {'breath':>9s} {'bpm':>7s} {'snr':>7s} {'gate':>7s}"
    print(header)
    print("-" * len(header))
    for room in result["rooms"]:
        print(
            f"{room['room']:32s} {room['presence']:8s} "
            f"{room['motion_cdb'] / 100.0:8.2f}dB {room['breath_energy_cdb'] / 100.0:8.2f}dB "
            f"{room['breath_rate_bpm']:7.2f} {room['breath_snr_db']:6.2f}dB {room['p0_verdict']:>7s}"
        )
    print()
    for room in result["rooms"]:
        res = room["resonance"]
        print(f"{room['room']}")
        print(f"    anchor   {room['anchor']}")
        print(f"    prev     {room['prev_anchor']}")
        print(f"    resonance bpm={res.get('bpm'):.1f} root={res.get('root_frequency'):.1f}Hz "
              f"intensity={res.get('intensity'):.3f} ({res.get('source')})")
        print(f"    P1 memory root {room['memory_root']}  recall verified: {room['recalled_matches']}")
        print(f"    chain valid: {room['report']['chain_valid']}  cells: {room['report']['cells']}")
    print()
    print("Nothing was pushed or published. Anchors above are reproducible:")
    print("    python tools/build_erb_vectors.py --check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
