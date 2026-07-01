# Protocol 6 — Hardware Attestation (stub)

**Signature:** Δ9Φ963-P6-ATTEST-STUB-v1

Zero-trust hardware fingerprint seal used as a P0 sub-key. If the host signature changes (migration, VM swap), P0 must re-validate before emitting the Resonance Badge.

**Status:** Architectural stub — do not enable in production until GitHub Pages + Grokipedia implementation section + three-way SHA lock are live.

```bash
python protocol6_quantum_attest/harness/run_attest_demo.py
```