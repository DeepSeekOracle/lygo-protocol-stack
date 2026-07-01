# P0 Nano Kernel — hardening (Grok builder spec)

## Deliverables

| Asset | Purpose |
|-------|---------|
| `fixtures/p0_vectors.json` | **42** vectors: canonical, boundary, adversarial, high-entropy, recursive, structured |
| `fixtures/p0_vectors.tsv` | Manifest for C/Rust harnesses |
| `fixtures/p0_canonical.sha256` | Golden SHA-256 of canonical stdout (Python ≡ Rust) |
| `tools/run_p0_demo.py` | CLI: input, `phi_risk`, decision, reasoning per vector |
| `tools/p0_crosslang_parity.py` | Lock Python / C / Rust canonical line hash |
| `src/c/lygo_p0_harness.c` | C port runner (pairs with `lygo_p0_nano.c`) |
| `src/rust/src/bin/p0_harness.rs` | Rust port runner |

## Quick start

```bash
python tools/build_p0_vectors.py
python tools/run_p0_demo.py              # full narrative demo
python tools/run_p0_demo.py --id json_minimal
python tools/p0_crosslang_parity.py      # SHA parity (install gcc for C)
python -m pytest protocol0_nano_kernel/tests/ -q
```

## Canonical line format (determinism)

Each vector emits one line (no reasoning — stable hash):

```
{id}|{VERDICT}|{risk:.4f}|{entropy:.4f}|{compression:.4f}|{phi_risk:.4f}
```

Math uses **IEEE754 f32 semantics** in Python (`struct.pack('<f')`) so firmware C/Rust match the reference.

## Vector categories (42)

- **canonical** — README regression set  
- **boundary** — lengths 0…8192, at `MAX_BYTES`  
- **recursive** — repeated windows / nested JSON  
- **adversarial** — `0xFF`, mono-byte, UTF-8 stress  
- **high_entropy** — SHA-derived & byte-walk payloads  
- **structured** — BMP/PE/XML-like stubs  

## Φ-gate reasoning

Every `validate_bytes()` result includes:

- `phi_risk` — `risk × Φ_max × size_damp`  
- `reasoning` — entropy band, compression score, Φ thresholds, low-entropy guard  

## Cross-language parity

Golden digest (Python + Rust verified):

```
7e8d18fda979cbefec14c3fc86f43f2a020b494b6052acccb6f865f2b4fae1d3
```

Install **gcc** (C) and **rustup** (Rust) for tri-language checks in CI or locally.

**Resonance signature:** Δ9Φ963-P0-HARDEN-v1.0