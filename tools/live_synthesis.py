#!/usr/bin/env python3
"""LYGO Phase 9 — live biometric seed → LDQ friction audio (WAV)."""

from __future__ import annotations

import argparse
import json
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from protocol8_ldq_synthesis import FrictionCore, HarmonicGravity, LYRASequencer, P8_VERSION  # noqa: E402

P0_GOLDEN = ROOT / "protocol0_byte_entropy_filter" / "fixtures" / "p0_canonical.sha256"
DEFAULT_SEED_PATH = ROOT / "tools" / "lygo_control_center" / "workspace" / "latest_seed.json"
P9_SYNTH_VERSION = "Δ9Φ963-PHASE9-SYNTH-v1.0"


def _default_seed_hex() -> str:
    if DEFAULT_SEED_PATH.is_file():
        try:
            data = json.loads(DEFAULT_SEED_PATH.read_text(encoding="utf-8"))
            seed = data.get("seed") or data.get("seed_hex")
            if seed:
                return str(seed).replace("0x", "")[:64]
        except json.JSONDecodeError:
            pass
    if P0_GOLDEN.is_file():
        return P0_GOLDEN.read_text(encoding="utf-8").strip().split()[0][:16]
    return "7e8d18fda979cbef"


def generate_audio_from_seed(
    seed_hex: str,
    output_file: str | Path = "synthesis_output.wav",
    *,
    duration_sec: float = 5.0,
    sample_rate: int = 44100,
) -> dict:
    clean = str(seed_hex).replace("0x", "").strip()
    seed_int = int(clean[:16], 16) if clean else 0
    gravity = HarmonicGravity(seed_int)
    params = gravity.get_all_parameters()
    root_freq = params["root_frequency"]
    intensity = params["intensity"]
    friction = FrictionCore(phi_risk=0.618)
    sequencer = LYRASequencer(seed_int)
    structure = sequencer.generate_structure(num_blocks=8)

    n = int(sample_rate * duration_sec)
    t = np.linspace(0.0, duration_sec, n, endpoint=False)
    signal = np.zeros(n, dtype=np.float64)
    block_len = max(1, n // len(structure))
    for i, block in enumerate(structure):
        start = i * block_len
        end = min(n, (i + 1) * block_len)
        seg_t = t[start:end]
        partial = block["gate"] / 9.0
        freq = root_freq * (1.0 + partial * 0.12)
        amp = intensity * (1.2 if block["accent"] else 0.85)
        signal[start:end] = amp * np.sin(2.0 * np.pi * freq * seg_t)
    signal = friction.process(signal)
    peak = float(np.max(np.abs(signal))) or 1.0
    signal = signal / peak
    out = Path(output_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes((signal * 32767.0).astype(np.int16).tobytes())
    return {
        "ok": True,
        "output": str(out.resolve()),
        "duration_sec": duration_sec,
        "sample_rate": sample_rate,
        "samples": n,
        "root_frequency": root_freq,
        "blocks": len(structure),
        "seed_hex_prefix": clean[:16],
        "signature": P9_SYNTH_VERSION,
        "ldq": P8_VERSION,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO live LDQ synthesis")
    ap.add_argument("--seed", default=None)
    ap.add_argument("--output", default="synthesis_output.wav")
    ap.add_argument("--duration", type=float, default=5.0)
    args = ap.parse_args()
    seed = args.seed or _default_seed_hex()
    result = generate_audio_from_seed(seed, args.output, duration_sec=args.duration)
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())