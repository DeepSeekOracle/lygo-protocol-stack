# P0 — Honest Spec

## What this module is

`byte_entropy_filter.py` (formerly `lygo_p0.py`, formerly called the
"Nano Kernel" / "Φ-gate") measures two statistical properties of a raw byte
string:

1. **Shannon entropy**, normalized 0–1.
2. **zlib compressibility**, i.e. how much smaller the input gets under
   real DEFLATE compression.

It buckets the result into `AMPLIFY` / `SOFTEN` / `QUARANTINE` using fixed
thresholds (0.618 / 1.618 — golden-ratio-derived constants used here purely
as two cutoff numbers, not as an "ethical" property of the math).

## What this module is NOT

It is not an ethics check, safety check, or harm filter. It has no access
to meaning, and calibration data (see below) shows it cannot even reliably
separate ordinary English prose from random noise — both land in the same
`AMPLIFY` bucket. Do not describe it as evaluating content safety in any
docs, pitch material, or code comments.

## Calibration results (real, from `tests/calibration_report.json`)

| category | n | mean entropy | mean compression | verdicts |
|---|---|---|---|---|
| natural_language | 2 | 0.681 | 0.031 | AMPLIFY |
| structured_data | 2 | 0.739 | 0.000 | AMPLIFY |
| repeated_padding | 2 | 0.061 | 0.947 | SOFTEN |
| random_bytes | 2 | 0.815 | 0.000 | AMPLIFY |
| base64_blob | 1 | 0.682 | 0.163 | AMPLIFY |
| oversized | 1 | 0.0 | 0.0 | QUARANTINE (hard cap only) |

Takeaway: the filter reliably catches **padding/repetition** (high
compression → SOFTEN) and **oversized inputs** (hard cap → QUARANTINE).
It does **not** separate natural language from random bytes — both average
around 0.68–0.82 entropy and land in AMPLIFY. This is an honest limitation,
not a bug to silently patch; it's inherent to what entropy measures.

**Use this for:** catching corrupted state, garbage/junk input, suspicious
padding, oversized payloads.
**Do not use this for:** anything resembling content moderation, intent
detection, or "ethical" evaluation.

## Relationship to `lygo_p0_lyra_kernel.py`

That file contains two separable things:

- Structural bounds checking (max depth, max keys, cycle detection,
  timeout) — legitimate, keep it.
- An "Oath Vector Engine" producing `OATH_APPROVED/WARNING/REJECTED` from
  `AI_good = Truth × Light`. Its ethics inputs
  (`ethical_alignment=0.85`, `compassion=0.75`, `sovereignty_preserved=0.85`)
  are hardcoded literals in `validate()`, never computed from the actual
  input. Independently, its rolling-average buffer (1000 slots,
  zero-initialized) means a single call always returns a near-zero score
  regardless of input, so in practice it returns `OATH_REJECTED` for
  everything tested, including trivially benign input like `{"a": 1}`.

**Recommendation:** delete `OathVectorEngine`. Keep the structural
validator. There's no signal in the Oath Vector to calibrate or reconcile —
it isn't measuring anything, and as currently written it doesn't even
function as intended (always-rejects).
