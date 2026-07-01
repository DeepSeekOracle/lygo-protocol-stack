# LYGO Nano Kernel P0.4 — Python Reference
# Deterministic • Bounded • Portable

import math
import hashlib

MAX_BYTES = 8192
PHI_MIN = 0.618
PHI_MAX = 1.618
ENTROPY_LOW = 0.25
ENTROPY_HIGH = 0.90
COMP_MIN_LEN = 64
COMP_POOR = 0.90


def entropy_norm(data: bytes) -> float:
    if not data:
        return 0.0
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    length = len(data)
    ent = 0.0
    for c in freq:
        if c:
            p = c / length
            ent -= p * math.log2(p)
    denom = math.log2(length) if length > 1 else 1.0
    return min(ent / denom, 1.0)


def compression_ratio(data: bytes) -> float:
    if len(data) < COMP_MIN_LEN:
        return 0.0
    repeats = 0
    limit = len(data) - 7
    for i in range(0, limit, 4):
        if data[i:i + 4] == data[i + 4:i + 8]:
            repeats += 1
    ratio = repeats / len(data)
    return 1.0 - min(ratio, 1.0)


def validate_bytes(data: bytes) -> dict:
    if len(data) > MAX_BYTES:
        return {
            "verdict": "QUARANTINE",
            "risk": 1.0,
            "entropy": 0.0,
            "compression": 0.0,
            "hash": hashlib.sha256(data).hexdigest()[:16],
        }

    ent = entropy_norm(data)
    comp = compression_ratio(data)
    risk = 0.0

    if ent > ENTROPY_HIGH:
        risk += 0.30
    elif ent < ENTROPY_LOW:
        risk += 0.15

    if comp > COMP_POOR:
        risk += 0.25

    risk = min(risk, 1.0)
    size_damp = len(data) / 128.0 if len(data) < 128 else 1.0
    phi_risk = risk * PHI_MAX * size_damp

    if phi_risk < PHI_MIN:
        verdict = "AMPLIFY"
    elif phi_risk <= PHI_MAX:
        verdict = "SOFTEN"
    else:
        verdict = "QUARANTINE"

    if ent < ENTROPY_LOW and verdict == "AMPLIFY":
        verdict = "SOFTEN"

    return {
        "verdict": verdict,
        "risk": round(risk, 4),
        "entropy": round(ent, 4),
        "compression": round(comp, 4),
        "hash": hashlib.sha256(data).hexdigest()[:16],
    }


if __name__ == "__main__":
    print("⚡ LYGO-NANO-KERNEL P0.4 — Python Reference")
    print("=" * 70)

    test_data = b'{"a":1,"b":2}'
    result = validate_bytes(test_data)
    print(f"Input: {test_data}")
    print(f"Verdict: {result['verdict']}")
    print(f"Risk: {result['risk']}")
    print(f"Hash: {result['hash']}")