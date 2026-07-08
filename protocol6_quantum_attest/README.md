# Protocol 6 — Hardware Attestation

**Signature:** `Δ9Φ963-PHASE6-v1.0`

Measurement pipeline, signed attestation badges, and peer verification. Software-complete; Keylime TPM quotes and FPGA PUF pending hardware.

## Quick start

```bash
pip install -e .  # optional; repo root on PYTHONPATH is enough
python tools/verify_hardware_attestation.py
python tools/run_phase6_audit.py
python protocol6_quantum_attest/harness/run_attest_demo.py
```

## Layout

See `docs/PHASE6_ARCHITECTURE.md`.

## Node API

- `GET /attestation/health`
- `GET /attestation/badge`
- `POST /attestation/verify`