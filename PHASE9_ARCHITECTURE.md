# Phase 9 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ WIDE-AREA MESH (HTTPS node_api_server + SLM gossip)         │
│   TLS pins in certs/pins.json + POST /gossip/pin            │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ HARDWARE ATTESTATION (P6 + keylime_bridge)                  │
│   measurement.tpm_quote → badge HMAC + ethical gate           │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ LIVE SYNTHESIS (P7 seed → P8 LDQ → WAV)                     │
│   HarmonicGravity → FrictionCore → LYRASequencer            │
└─────────────────────────────────────────────────────────────┘
```

## Trust boundaries

- **P0 golden hash** remains the root of trust for badges; quotes augment measurement bundle.
- **TLS pins** are mesh-local trust-on-first-use; rotation via `tls_manager.rotate()`.
- **Synthesis** is deterministic from seed prefix (auditable, no hidden RNG).

## Integration points

- `stack/lygo_stack.py` — unchanged surface; badges pick up quotes via `MeasurementCollector`.
- `stack/sovereign_lattice_mesh.py` — Merkle gossip can carry pin metadata in future extension.
- HF Space — bundle includes `protocol8_ldq_synthesis` and Phase 9 tools.