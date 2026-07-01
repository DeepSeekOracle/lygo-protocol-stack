# Protocol 0: Nano Kernel

The Nano Kernel is the ethical gate for the LYGO stack. It accepts a bounded byte payload and returns a verdict:

- **AMPLIFY** — safe to propagate
- **SOFTEN** — reduce intensity / add guardrails
- **QUARANTINE** — block and isolate

## Φ-Gate

Risk is computed from normalized entropy and a lightweight compression heuristic, then scaled by golden-ratio bounds (`PHI_MIN`, `PHI_MAX`) with size damping for small inputs.

## Ports

| Path | Language |
|------|----------|
| `src/python/lygo_p0.py` | Reference harness |
| `src/c/lygo_p0.c` | Firmware-safe C |
| `src/rust/src/lib.rs` | `#![no_std]` Rust |
| `src/hardware/README.md` | FPGA integration notes |