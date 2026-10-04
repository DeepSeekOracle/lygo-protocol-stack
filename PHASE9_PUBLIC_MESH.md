# Phase 9 — Public Mesh Deployment

**Signature:** `Δ9Φ963-PHASE9-v1.0`  
**Blueprint:** Lightfather's Voice — Next Blueprint (wide-area TLS, Keylime TPM, live LDQ synthesis)

## Objectives

1. **TLS 1.2+** node API with self-signed PKI, pin gossip, rotation.
2. **Hardware attestation** enriched with Keylime TPM quotes (simulated when no agent).
3. **Live synthesis** — P7 biometric seed → Protocol 8 LDQ → WAV output.

## Modules

| Module | Path |
|--------|------|
| TLS manager | `tools/tls_manager.py` |
| Keylime bridge | `protocol6_quantum_attest/keylime_bridge.py` |
| TPM CLI | `tools/tpm_attestation.py` |
| LDQ synthesis | `protocol8_ldq_synthesis/` |
| Live runner | `tools/live_synthesis.py` |
| Audit | `tools/run_phase9_audit.py` |

## API (node)

- `GET /cert/pin` — local pin + expiry
- `POST /cert/pin` · `POST /gossip/pin` — ingest peer pin
- `POST /synthesis/run` — `{seed?, duration_sec?, output?}`

Start HTTPS: `python tools/node_api_server.py --tls --port 8443`

## Verification

```bash
pip install -r requirements-phase9.txt
python tools/run_phase9_audit.py
python -m pytest tests/test_phase9_public_mesh.py -q
```

Artifact: `tests/phase9_audit_last_run.json`

## Security notes

- Pins use **SHA-256(DER)** of peer certificates.
- Set `LYGO_KEYLIME_FORCE_SIM=0` to prefer live Keylime agent (localhost:9002).
- Wide-area production still requires operator TLS policy and CA strategy (human gate).