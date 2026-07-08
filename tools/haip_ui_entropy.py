"""Gradio/HF helpers — map UI telemetry params to Python P7 entropy extraction."""

from __future__ import annotations

import random
from typing import Any


def synthetic_ibi_from_ui(
    bpm: float,
    sdnn: float,
    noise_pct: float,
    *,
    n: int = 24,
    seed: int = 963528174,
) -> list[float]:
    rng = random.Random(seed + int(bpm) + int(sdnn))
    ibi: list[float] = []
    for _ in range(n):
        ibi.append(60000.0 / max(40.0, bpm) + rng.uniform(-sdnn, sdnn) * (1.0 + noise_pct / 100.0))
    return ibi


def compute_harness_report(
    bpm: float,
    sdnn: float,
    noise_pct: float,
    fs_hz: float,
) -> dict[str, Any]:
    from protocol7_human_ai_interface.entropy_extraction import extract_p0_seed_from_ibi
    from protocol7_human_ai_interface.ethical_mapping import EthicalVectorMapper

    ibi = synthetic_ibi_from_ui(bpm, sdnn, noise_pct)
    extraction = extract_p0_seed_from_ibi(ibi)
    agg = {
        "heart_rate": bpm,
        "hrv": sdnn,
        "stress_level": min(1.0, noise_pct / 50.0),
        "activity_steps": 5000,
        "battery": 0.75,
    }
    state = {"timestamp": 0, "aggregated": agg, "ibi_ms": ibi}
    mapper = EthicalVectorMapper()
    ev = mapper.map_to_ethical_vector(state)
    freq = mapper.map_to_frequency(ev)
    light = mapper.light_code_from_state(state, ev)
    h_min_ui = max(0.0, 0.95 - (noise_pct / 600.0) - (sdnn / 2000.0))

    return {
        "signature": "Δ9Φ963-PHASE7-v1.0",
        "telemetry": {"bpm": bpm, "sdnn_ms": sdnn, "noise_pct": noise_pct, "fs_hz": fs_hz},
        "h_min_python": extraction["h_min"],
        "h_min_ui_formula": round(h_min_ui, 4),
        "seed_256": extraction["seed_256"],
        "ethical_vector": ev,
        "frequency_hz": freq,
        "light_code": light,
        "ibi_sample_ms": [round(x, 1) for x in ibi[:8]],
        "pages_harness": "https://deepseekoracle.github.io/lygo-protocol-stack/BiometricEntropyHarness.html",
        "excavationpro_mirror": "https://deepseekoracle.github.io/Excavationpro/BiometricEntropyHarness.html",
    }


def format_markdown_report(report: dict[str, Any]) -> str:
    return (
        f"### Phase 7 — Python stack parity\n"
        f"**H_min (extractor):** `{report['h_min_python']}` · "
        f"**UI formula:** `{report['h_min_ui_formula']}`\n\n"
        f"**P0 seed (HMAC-SHA256):** `{report['seed_256']}`\n\n"
        f"**Ethical vector** [Truth, Love, Freedom]: `{report['ethical_vector']}`\n"
        f"**Solfeggio:** `{report['frequency_hz']}` Hz · **Light code:** `{report['light_code']}`\n\n"
        f"IBI sample (ms): `{report['ibi_sample_ms']}`\n\n"
        f"Interactive UI: [GitHub Pages harness]({report['pages_harness']}) · "
        f"[Excavationpro mirror]({report['excavationpro_mirror']})"
    )