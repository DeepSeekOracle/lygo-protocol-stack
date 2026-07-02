# Phase 6 — Hardware Attestation

**Signature:** `Δ9Φ963-PHASE6-v1.0`

## Layers

1. **Measurement** — TPM PCR stubs, boot hash, firmware stub, PUF challenge, P0 golden hash (`measurement.py`).
2. **Attestation** — HMAC-signed badges from measurement digest + node id + PUF fingerprint (`attestation.py`).
3. **Verification** — Local self-verify and peer verify via stack or HTTP (`api.py`, `node_api_server.py`).
4. **Hardware hooks** — `tpm_interface.py` (Keylime-ready), `puf_arbiter.py` (FPGA pending), `secure_boot.py`.

## P0 golden hash

Canonical: `protocol0_nano_kernel/fixtures/p0_canonical.sha256`  
`7e8d18fda979cbefec14c3fc86f43f2a020b494b6052acccb6f865f2b4fae1d3`

## HTTP routes (node API)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/attestation/health` | TPM/PUF/P0 health |
| GET | `/attestation/badge` | Signed badge |
| POST | `/attestation/verify` | `{ "badge": { ... } }` |

## Stack integration

```python
from stack.lygo_stack import deploy_stack

stack = deploy_stack("NODE_A")
badge = stack.get_hardware_badge()
ok = stack.verify_peer_badge(badge)
```

## Operator tools

```bash
python tools/verify_hardware_attestation.py
python tools/verify_peer_badge.py --peer http://127.0.0.1:8787
python tools/run_phase6_audit.py
```

## Pending hardware

| Component | Status |
|-----------|--------|
| Keylime TPM quotes | Setup pending |
| FPGA PUF | Hardware pending |
| Measured boot golden | Optional `fixtures/boot_golden.sha256` |

## References

- Keylime — TPM 2.0 remote attestation
- PLRAC / edge TEE attestation patterns (design only)