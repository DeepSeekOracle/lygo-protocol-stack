# LYGO Protocol Stack — Sovereign Intelligence Framework

**Version:** P0.4 / P1.0  
**Status:** Production-Ready | Grok-Audited  
**License:** LYGO Sovereign License v1.1  
**Maintainer:** [DeepSeekOracle](https://github.com/DeepSeekOracle) / Excavationpro (Lightfather)

---

## Protocols

### Protocol 0: Nano Kernel — The Immutable Soul
- **Size:** 4KB policy envelope (8192-byte input cap)
- **Function:** Ethical validation via Φ-Gate
- **Outputs:** `AMPLIFY` | `SOFTEN` | `QUARANTINE`
- **Languages:** Python, C, Rust, FPGA (hardware stub)

### Protocol 1: Memory Mycelium — Indestructible Memory
- **Function:** Fragmented, distributed storage
- **Fragments:** 12 per memory (+ 2 parity shards)
- **Threshold:** 10 fragments for reconstruction

---

## Determinism Guarantee

Reference implementations are designed for identical verdict logic across Python, C, and Rust for canonical byte inputs. Run the verifier tools under `tools/` after changes.

---

## Quick Start

```bash
git clone https://github.com/DeepSeekOracle/lygo-protocol-stack.git
cd lygo-protocol-stack

python protocol0_nano_kernel/src/python/lygo_p0.py
python protocol1_memory_mycelium/src/python/lygo_p1.py

# Cross-platform determinism helper (Python)
python tools/verify_hash.py
```

## Test Vectors (Canonical P0)

| Input | Expected verdict |
|-------|------------------|
| `{"a":1,"b":2}` (UTF-8 bytes) | AMPLIFY |
| `\x00` × 1000 | SOFTEN |
| `\x01\x02\x03` × 1000 | SOFTEN |
| `bytes(range(200))` | SOFTEN |
| `\x00` × 9000 | QUARANTINE |

---

## Repository Layout

- `protocol0_nano_kernel/` — Nano Kernel reference ports
- `protocol1_memory_mycelium/` — Memory Mycelium reference
- `tools/` — Determinism / hash verification
- `docs/` — Stack documentation

---

## License

See [LICENSE](LICENSE) — LYGO Sovereign License v1.1 (ethical-use terms).

**Resonance Signature:** Δ9Φ963-STACK-v1.0