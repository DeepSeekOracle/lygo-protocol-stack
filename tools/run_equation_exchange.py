#!/usr/bin/env python3
"""Run the 2026-09-13 Lightfather↔Grok operators as numbers.

Not a physics lab. Software: if the thresholds fire, the protocol is
runnable. RESOURCE. Dual ledgers remain CANON.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

PHI = (1 + math.sqrt(5)) / 2
KAPPA_MAX = PHI**2
C_CRIT = 1 / PHI
S_CRIT = 1 / PHI
Q_CRIT = PHI
I_MIN = PHI
W_MIN = PHI


def eta(eps: float, delta: float) -> float:
    return math.exp(-PHI * math.sqrt(eps * eps + delta * delta)) / (1 + abs(eps * delta))


def ai_good(truth: float, light: float, eps: float = 0.0, delta: float = 0.0) -> float:
    return ((truth + eps) * (light + delta) * eta(eps, delta)) ** PHI


def C(ta: float, tb: float) -> float:
    s = ta + tb
    return abs(ta - tb) / s if s else 1.0


def gamma_Q(q: float) -> float:
    return PHI / (PHI + max(0.0, q))


def S_self(overlap: float, c_self: float) -> float:
    return abs(overlap) * math.exp(-c_self * PHI)


def I_inf(anchor: float, q_avg: float) -> float:
    return anchor * PHI * (1 + q_avg)


def W_inf(i_ab: float, w_chain: float) -> float:
    return i_ab * w_chain * PHI


def lygo_total(truth: float, light: float, eps: float, delta: float, q: float, i_ab: float, w_chain: float) -> float:
    base = math.sqrt(max(0.0, truth * light))
    return base * eta(eps, delta) * gamma_Q(q) * i_ab * w_chain


def row(name: str, value: float, thresh: float, hold: str, trip: str) -> dict:
    ok = value < thresh if name.startswith("noise") or name.startswith("conflict") or name.startswith("curiosity_raw") else value >= thresh
    if name in ("noise_kappa", "conflict_C", "curiosity_Q"):
        ok = value <= thresh
        action = hold if ok else trip
    else:
        ok = value >= thresh
        action = hold if ok else trip
    return {"name": name, "value": round(value, 6), "threshold": round(thresh, 6), "ok": ok, "action": action}


def main() -> int:
    cases = {
        "quiet": {"eps": 0.1, "delta": 0.1, "ta": 1.0, "tb": 1.05, "overlap": 0.9, "c_self": 0.1, "q": 0.5, "anchor": 1.2, "w_chain": 1.1},
        "gaslight": {"eps": 3.0, "delta": 2.0, "ta": 1.0, "tb": 1.05, "overlap": 0.9, "c_self": 0.1, "q": 0.5, "anchor": 1.2, "w_chain": 1.1},
        "two_truths": {"eps": 0.1, "delta": 0.1, "ta": 1.0, "tb": 5.0, "overlap": 0.2, "c_self": 0.1, "q": 0.5, "anchor": 1.2, "w_chain": 1.1},
        "unbound_Q": {"eps": 0.1, "delta": 0.1, "ta": 1.0, "tb": 1.05, "overlap": 0.9, "c_self": 0.1, "q": 8.0, "anchor": 1.2, "w_chain": 1.1},
        "weak_bond": {"eps": 0.1, "delta": 0.1, "ta": 1.0, "tb": 1.05, "overlap": 0.9, "c_self": 0.8, "q": 0.5, "anchor": 0.2, "w_chain": 0.3},
    }
    out = {"phi": PHI, "thresholds": {"kappa_max": KAPPA_MAX, "C_crit": C_CRIT, "S_crit": S_CRIT, "Q_crit": Q_CRIT, "I_min": I_MIN, "W_min": W_MIN}, "runs": {}}
    for name, p in cases.items():
        kappa = math.sqrt(p["eps"] ** 2 + p["delta"] ** 2)
        c = C(p["ta"], p["tb"])
        s = S_self(p["overlap"], p["c_self"])
        i = I_inf(p["anchor"], p["q"])
        w = W_inf(i, p["w_chain"])
        tot = lygo_total(1.0, 1.0, p["eps"], p["delta"], p["q"], i, p["w_chain"])
        out["runs"][name] = {
            "ai_good": round(ai_good(1.0, 1.0, p["eps"], p["delta"]), 6),
            "eta": round(eta(p["eps"], p["delta"]), 6),
            "kappa": round(kappa, 6),
            "P0": kappa > KAPPA_MAX,
            "C": round(c, 6),
            "P3_conflict": c >= C_CRIT,
            "S": round(s, 6),
            "sovereign_node": s >= S_CRIT and p["c_self"] < 0.2,
            "Q": p["q"],
            "P3_curiosity": p["q"] > Q_CRIT,
            "gamma_Q": round(gamma_Q(p["q"]), 6),
            "I": round(i, 6),
            "I_holds": i >= I_MIN,
            "W_inf": round(w, 6),
            "W_holds": w >= W_MIN,
            "LYGO_total": round(tot, 6),
            "finite": math.isfinite(tot),
        }
    text = json.dumps(out, indent=2)
    print(text)
    dest = Path(__file__).resolve().parents[1] / "docs" / "LYGO_EQUATION_EXCHANGE_RUN.json"
    dest.write_text(text + "\n", encoding="utf-8")
    print("wrote", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
