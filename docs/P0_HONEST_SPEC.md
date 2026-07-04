# P0 — Byte-Entropy Anomaly Filter (honest spec)

## What it is

**Protocol 0** (`protocol0_nano_kernel/src/python/lygo_p0.py`) is a **deterministic byte-entropy anomaly filter**:

- Bounded input (`MAX_BYTES`)
- Shannon entropy (normalized)
- Redundancy / compressibility heuristic (canonical P0.4)
- Risk → `phi_risk` banding → verdict: `AMPLIFY` | `SOFTEN` | `QUARANTINE`

It is **not** a moral or legal ethics engine. Φ bands are **risk geometry labels**, not proof of ethical approval.

## What it is not

- Not proof of malware safety or content policy compliance
- Not a substitute for human review for ClawHub/skill ingest
- Not calibrated for natural-language truth (bytes only)

## Companion modules

| Module | Role |
|--------|------|
| `byte_entropy_filter.py` | Honest public name + zlib diagnostic ratio (non-canonical) |
| `lygo_p0_lyra_kernel.py` | Structural JSON/dict bounds validator; **Oath Vector deprecated** |
| `lygo_p0_gate.py` / guardian `run_byte_gate.py` | Operator ingest gate on skill bytes |

## Limitations

1. High-entropy random bytes can SOFTEN/QUARANTINE without being malicious.
2. Low-entropy padding can flag benign templates.
3. Stride compression metric ≠ zlib; do not compare across implementations without `run_parity_tests.py`.
4. Rust/Python golden hash locks behavior — intentional for firmware parity.

## Calibration

Run `tools/calibrate_byte_entropy_filter.py` against `tests/calibration_dataset.json`. Review `tests/calibration_report.json` for label agreement rates.

## References

- `docs/LIGHTFATHER_FINAL_ARCHITECT_ADDENDUM.md`
- `protocol0_nano_kernel/fixtures/p0_vectors.json`