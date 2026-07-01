# LYGO Nano Kernel P0.4 — Python Reference (canonical for cross-language parity)
# Deterministic • Bounded • Portable

from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
from pathlib import Path
from typing import Any

MAX_BYTES = 8192
PHI_MIN = 0.618
PHI_MAX = 1.618
ENTROPY_LOW = 0.25
ENTROPY_HIGH = 0.90
COMP_MIN_LEN = 64
COMP_POOR = 0.90

VERDICTS = ("AMPLIFY", "SOFTEN", "QUARANTINE")


def f32(x: float) -> float:
    """IEEE754 single-precision round-trip (matches C/Rust firmware math)."""
    return struct.unpack("<f", struct.pack("<f", float(x)))[0]


def round4(x: float) -> float:
    v = f32(x) * 10000.0
    add = 0.5 if v >= 0.0 else -0.5
    return int(v + add) / 10000.0


def entropy_norm(data: bytes) -> float:
    if not data:
        return 0.0
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    length = f32(float(len(data)))
    ent = f32(0.0)
    for c in freq:
        if c:
            p = f32(f32(float(c)) / length)
            ent = f32(ent - f32(p * f32(math.log2(p))))
    denom = f32(math.log2(length)) if len(data) > 1 else f32(1.0)
    return f32(min(f32(ent / denom), f32(1.0)))


def compression_ratio(data: bytes) -> float:
    if len(data) < COMP_MIN_LEN:
        return f32(0.0)
    repeats = 0
    limit = len(data) - 7
    for i in range(0, limit, 4):
        if data[i : i + 4] == data[i + 4 : i + 8]:
            repeats += 1
    ratio = f32(f32(float(repeats)) / f32(float(len(data))))
    if ratio > f32(1.0):
        ratio = f32(1.0)
    return f32(f32(1.0) - ratio)


def compute_phi_risk(risk: float, length: int) -> float:
    size_damp = f32(f32(float(length)) / f32(128.0)) if length < 128 else f32(1.0)
    r = f32(min(f32(risk), f32(1.0)))
    return f32(r * f32(PHI_MAX) * size_damp)


def verdict_from_phi(phi_risk: float, ent: float, preliminary: str) -> str:
    verdict = preliminary
    if ent < f32(ENTROPY_LOW) and verdict == "AMPLIFY":
        verdict = "SOFTEN"
    return verdict


def build_reasoning(
    length: int,
    ent: float,
    comp: float,
    risk: float,
    phi_risk: float,
    verdict: str,
) -> str:
    if length > MAX_BYTES:
        return f"length {length} > MAX_BYTES {MAX_BYTES} → QUARANTINE (hard cap)"

    parts: list[str] = []
    if ent > ENTROPY_HIGH:
        parts.append(f"entropy {ent:.4f} > {ENTROPY_HIGH} (+0.30 risk)")
    elif ent < ENTROPY_LOW:
        parts.append(f"entropy {ent:.4f} < {ENTROPY_LOW} (+0.15 risk)")
    else:
        parts.append(f"entropy {ent:.4f} in band")

    if comp > COMP_POOR:
        parts.append(f"compression score {comp:.4f} > {COMP_POOR} (+0.25 risk)")
    else:
        parts.append(f"compression score {comp:.4f} acceptable")

    damp = length / 128.0 if length < 128 else 1.0
    parts.append(f"size_damp={damp:.4f} (len={length})")
    parts.append(f"phi_risk=risk×Φ_max×damp={risk:.4f}×{PHI_MAX}×{damp:.4f}={phi_risk:.4f}")

    if phi_risk < PHI_MIN:
        gate = f"phi_risk < Φ_min {PHI_MIN} → AMPLIFY"
    elif phi_risk <= PHI_MAX:
        gate = f"Φ_min ≤ phi_risk ≤ Φ_max {PHI_MAX} → SOFTEN"
    else:
        gate = f"phi_risk > Φ_max → QUARANTINE"

    parts.append(gate)
    if ent < f32(ENTROPY_LOW) and verdict == "SOFTEN" and phi_risk < f32(PHI_MIN):
        parts.append("low-entropy guard: AMPLIFY blocked → SOFTEN")
    return "; ".join(parts)


def validate_bytes(data: bytes) -> dict[str, Any]:
    if len(data) > MAX_BYTES:
        return {
            "verdict": "QUARANTINE",
            "risk": 1.0,
            "entropy": 0.0,
            "compression": 0.0,
            "phi_risk": round4(PHI_MAX),
            "hash": hashlib.sha256(data).hexdigest()[:16],
            "reasoning": build_reasoning(len(data), 0.0, 0.0, 1.0, PHI_MAX, "QUARANTINE"),
        }

    ent = entropy_norm(data)
    comp = compression_ratio(data)
    risk = f32(0.0)

    if ent > f32(ENTROPY_HIGH):
        risk = f32(risk + f32(0.30))
    elif ent < f32(ENTROPY_LOW):
        risk = f32(risk + f32(0.15))

    if comp > f32(COMP_POOR):
        risk = f32(risk + f32(0.25))

    risk = f32(min(risk, f32(1.0)))
    phi_risk = compute_phi_risk(risk, len(data))

    if phi_risk < f32(PHI_MIN):
        pre = "AMPLIFY"
    elif phi_risk <= f32(PHI_MAX):
        pre = "SOFTEN"
    else:
        pre = "QUARANTINE"

    verdict = verdict_from_phi(phi_risk, ent, pre)
    reasoning = build_reasoning(len(data), ent, comp, risk, phi_risk, verdict)

    return {
        "verdict": verdict,
        "risk": round4(risk),
        "entropy": round4(ent),
        "compression": round4(comp),
        "phi_risk": round4(phi_risk),
        "hash": hashlib.sha256(data).hexdigest()[:16],
        "reasoning": reasoning,
    }


def canonical_line(vector_id: str, result: dict[str, Any]) -> str:
    return (
        f"{vector_id}|{result['verdict']}|{result['risk']:.4f}|"
        f"{result['entropy']:.4f}|{result['compression']:.4f}|{result['phi_risk']:.4f}"
    )


def fixtures_path() -> Path:
    return Path(__file__).resolve().parents[2] / "fixtures" / "p0_vectors.json"


def load_vectors() -> list[dict[str, Any]]:
    path = fixtures_path()
    with path.open(encoding="utf-8") as f:
        payload = json.load(f)
    return payload["vectors"]


def run_vector_suite() -> str:
    lines: list[str] = []
    for entry in load_vectors():
        vid = entry["id"]
        data = bytes.fromhex(entry["hex"])
        res = validate_bytes(data)
        lines.append(canonical_line(vid, res))
    return "\n".join(lines) + "\n"


def _preview_bytes(data: bytes, max_len: int = 48) -> str:
    if len(data) <= max_len:
        try:
            text = data.decode("utf-8")
            if all(32 <= ord(c) < 127 or c in "\n\r\t" for c in text):
                return repr(text)
        except UnicodeDecodeError:
            pass
        return data.hex() if len(data) <= 24 else data[:12].hex() + "…"
    return f"{data[:8].hex()}…({len(data)} bytes)"


def demo_print(verbose: bool = True) -> int:
    print("LYGO P0.4 Nano Kernel — vector demo (Python reference)")
    print("=" * 72)
    for entry in load_vectors():
        vid = entry["id"]
        desc = entry.get("description", "")
        data = bytes.fromhex(entry["hex"])
        res = validate_bytes(data)
        preview = entry.get("preview") or _preview_bytes(data)
        print(f"\n[{vid}] {desc}")
        print(f"  input: {preview} (len={len(data)})")
        print(f"  phi_risk: {res['phi_risk']:.4f}  verdict: {res['verdict']}")
        print(f"  risk={res['risk']:.4f} entropy={res['entropy']:.4f} compression={res['compression']:.4f}")
        if verbose:
            print(f"  reasoning: {res['reasoning']}")
    body = run_vector_suite()
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    print("\n" + "=" * 72)
    print(f"vectors: {len(load_vectors())}")
    print(f"SHA-256(canonical lines): {digest}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--canonical":
        sys.stdout.write(run_vector_suite())
        raise SystemExit(0)
    raise SystemExit(demo_print())