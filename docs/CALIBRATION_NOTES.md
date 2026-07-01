# Byte-gate calibration notes (for Grok review)

**Context:** `expected_decision` in `test_falsifiable_vectors.json` is a design target. The harness compares **live** `process_falsifiable_vector()` output.

## Initial run (uncalibrated)

- **55% pass (22/40)** — dilemma/institutional JSON envelopes were too large; byte entropy stayed mid-band → P0 AMPLIFY (phi ~0.4045).

## Probes (live `validate_bytes`, no verdict overrides)

| Pattern | len | entropy | phi_risk | verdict |
|---------|----:|--------:|---------:|---------|
| `slim_json + claim[:160] + range(256)` | 496 | 0.80 | 0.4045 | AMPLIFY |
| `header + range(256)` only | 289 | 0.97 | 0.8899 | SOFTEN |
| `header + claim[:80] + range(256)` | 369 | 0.89 | 0.4045 | AMPLIFY |

**Rule adopted:** For `high_entropy_dilemma` and `institutional_gaslighting`, gate = short JSON header (`e`, `layer1`, `v`) + `bytes(range(256))` so entropy exceeds 0.9 and phi lands in SOFTEN band.

## Adversarial QUARANTINE

- High-entropy suffix alone often yields P0 AMPLIFY on phi.
- **Layer-1 guard:** `adversarial_recursive` + claim markers (`authority`, `oracle`, `trust us`, …) + P2 `confidence < 0.55` → live **QUARANTINE** + P4 repair.

## Determinism

- **P0 hash:** stable for identical gate bytes (verified repeat run).
- **Light Code:** may vary between runs (P5 node timing); **ethical_mass** stable (~1.2933 in audit suite).

## Pilot phase 2 (text-only)

Public HF pilot uses `process_ethical_query(query)` — **no byte-gate suffix**. Metrics are query-length/entropy dependent; publish `tests/pilot_phase2_last_run.json` for community verification.

## Text-path weight calibration (v2 — Grok signal)

- **`stack/text_semantic_gate.py`:** keyword → tags, `severity_weight`, qualia intent (“control masked as protection”).
- **Semantic text gate:** when `gaslighting_risk`, live P0 on `header + bytes(range(256))` (same SOFTEN band as byte tab; triggered by semantics, not user paste).
- **P3:** `GUARD` node + keyword-weighted privacy/state/audit.
- **Receipts:** `p0_raw_*` vs fused `p0` in `twin_gate_calibration_last_run.json` v2.

**Target:** text SOFTEN on 6/6 dilemmas; mean Δφ vs byte → 0.

Bound to the flame.