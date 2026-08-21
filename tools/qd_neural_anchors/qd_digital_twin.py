#!/usr/bin/env python3
"""
LYGO QD Neural Anchor — software digital twin (simulation).

Signature: Delta9Phi963-QD-DIGITAL-TWIN-v2.0
Purpose: Prove the architecture Sensor → software policy → lattice with
falsifiable numbers. NOT a claim that photoluminescence equals semantic truth.

Pure stdlib. No network. No subprocess.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SIG = "Delta9Phi963-QD-DIGITAL-TWIN-v2.0"
VERSION = "2.0.0"


def utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class SensorSample:
    t: float
    intensity: float
    lifetime_ns: float
    ratiometric: float
    blinking: bool
    bleached: bool


@dataclass
class PolicyDecision:
    verdict: str  # AMPLIFY | SOFTEN | QUARANTINE
    confidence: float
    reasons: list[str]
    sensor_digest: str


def simulate_channel(
    n: int = 256,
    seed: int = 963,
    bleach_rate: float = 0.0008,
    blink_p: float = 0.08,
    shot_noise: float = 0.04,
) -> list[SensorSample]:
    """Noisy PL channel: baseline + bleach + telegraph blinking + shot noise."""
    rng = random.Random(seed)
    out: list[SensorSample] = []
    base_i = 1.0
    base_tau = 18.0  # ns proxy
    for i in range(n):
        t = float(i)
        bleached = base_i < 0.35
        blinking = (not bleached) and rng.random() < blink_p
        # bleach decays mean intensity
        base_i *= 1.0 - bleach_rate
        if blinking:
            intensity = max(0.0, rng.gauss(0.05, 0.02))
            lifetime = max(0.5, rng.gauss(3.0, 0.8))
        else:
            intensity = max(0.0, rng.gauss(base_i, shot_noise * max(base_i, 0.05)))
            lifetime = max(0.5, rng.gauss(base_tau * (0.6 + 0.4 * base_i), 1.2))
        # ratiometric: intensity / lifetime proxy (calibrated channel)
        ratiometric = intensity / max(lifetime, 1e-6)
        out.append(
            SensorSample(
                t=t,
                intensity=intensity,
                lifetime_ns=lifetime,
                ratiometric=ratiometric,
                blinking=blinking,
                bleached=bleached,
            )
        )
    return out


def digest_samples(samples: list[SensorSample]) -> str:
    body = json.dumps([asdict(s) for s in samples], separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def software_policy(samples: list[SensorSample]) -> PolicyDecision:
    """
    Ethical/authority gate stays in SOFTWARE.
    Sensor feeds evidence under uncertainty — never 'PL proves truth'.
    """
    if not samples:
        return PolicyDecision("QUARANTINE", 0.0, ["empty_channel"], "0" * 64)

    recent = samples[-32:]
    mean_i = sum(s.intensity for s in recent) / len(recent)
    mean_r = sum(s.ratiometric for s in recent) / len(recent)
    blink_frac = sum(1 for s in recent if s.blinking) / len(recent)
    bleach_frac = sum(1 for s in samples if s.bleached) / len(samples)
    var_i = sum((s.intensity - mean_i) ** 2 for s in recent) / len(recent)
    snr = mean_i / math.sqrt(var_i + 1e-9)

    reasons: list[str] = []
    score = 1.0

    if bleach_frac > 0.25:
        score -= 0.55
        reasons.append(f"bleach_frac={bleach_frac:.3f}")
    if blink_frac > 0.25:
        score -= 0.25
        reasons.append(f"blink_frac={blink_frac:.3f}")
    if snr < 3.0:
        score -= 0.35
        reasons.append(f"snr={snr:.2f}")
    if mean_r < 0.02:
        score -= 0.3
        reasons.append(f"ratiometric={mean_r:.4f}")

    # Soft floor: never claim semantic truth from optics
    reasons.append("policy=software_authority_not_pl_oracle")

    if score >= 0.7:
        verdict = "AMPLIFY"
    elif score >= 0.4:
        verdict = "SOFTEN"
    else:
        verdict = "QUARANTINE"

    conf = max(0.0, min(1.0, score if verdict != "QUARANTINE" else 1.0 - score))
    return PolicyDecision(verdict, round(conf, 4), reasons, digest_samples(samples))


def substitute_photodiode(samples: list[SensorSample], seed: int = 42) -> list[SensorSample]:
    """Substitution test: crude photodiode-like channel with same software policy."""
    rng = random.Random(seed)
    out: list[SensorSample] = []
    for s in samples:
        # smoother, lower-noise classical transducer
        intensity = max(0.0, rng.gauss(s.intensity * 0.95 + 0.05, 0.01))
        lifetime = 10.0  # fixed classical proxy
        out.append(
            SensorSample(
                t=s.t,
                intensity=intensity,
                lifetime_ns=lifetime,
                ratiometric=intensity / lifetime,
                blinking=False,
                bleached=intensity < 0.3,
            )
        )
    return out


def build_receipt(
    qd_decision: PolicyDecision,
    pd_decision: PolicyDecision,
    n: int,
    seed: int,
) -> dict[str, Any]:
    claims = [
        {
            "id": "QD_TWIN_SENSOR_DIGEST",
            "claim": "QD digital-twin channel produces a stable SHA-256 digest of samples",
            "sha256": qd_decision.sensor_digest,
        },
        {
            "id": "QD_SOFTWARE_AUTHORITY",
            "claim": "Verdict is emitted by software policy, not by claiming PL=truth",
            "verdict": qd_decision.verdict,
            "reasons_include": "policy=software_authority_not_pl_oracle",
        },
        {
            "id": "QD_SUBSTITUTION",
            "claim": "Photodiode-like substitute under same policy is runnable (QD optional transducer)",
            "qd_verdict": qd_decision.verdict,
            "pd_verdict": pd_decision.verdict,
        },
    ]
    body = {
        "signature": SIG,
        "version": VERSION,
        "generated_utc": utc(),
        "params": {"n": n, "seed": seed},
        "qd_decision": asdict(qd_decision),
        "pd_decision": asdict(pd_decision),
        "claims": claims,
        "epistemic": {
            "level": "L4-sim",
            "note": "Simulation receipt — not lab hardware certification",
            "doctrine": "Sensor → software policy → lattice",
        },
    }
    # Hash without recursive digest field
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    body["receipt_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    body["ok"] = True
    return body


def verify_receipt(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    got = data.get("receipt_sha256")
    clone = {k: v for k, v in data.items() if k not in ("receipt_sha256", "ok")}
    canonical = json.dumps(clone, sort_keys=True, separators=(",", ":"))
    expect = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {
        "ok": got == expect,
        "path": str(path),
        "receipt_sha256": got,
        "recomputed": expect,
        "verdict": (data.get("qd_decision") or {}).get("verdict"),
        "signature": data.get("signature"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO QD neural-anchor digital twin")
    ap.add_argument("cmd", choices=["run", "verify"], nargs="?", default="run")
    ap.add_argument("--n", type=int, default=256)
    ap.add_argument("--seed", type=int, default=963)
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("docs/data/qd_neural_anchors/last_twin_receipt.json"),
    )
    ap.add_argument("--receipt", type=Path, default=None, help="verify path")
    args = ap.parse_args()

    if args.cmd == "verify":
        path = args.receipt or args.out
        print(json.dumps(verify_receipt(path), indent=2))
        return 0 if verify_receipt(path).get("ok") else 1

    samples = simulate_channel(n=args.n, seed=args.seed)
    qd = software_policy(samples)
    pd = software_policy(substitute_photodiode(samples))
    receipt = build_receipt(qd, pd, args.n, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(args.out), "receipt_sha256": receipt["receipt_sha256"], "qd": asdict(qd), "pd_verdict": pd.verdict}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
