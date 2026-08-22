# Security — lygo-quantum-attestor v1.0.0

## Permissions

| Capability | Default |
|------------|---------|
| Network | **None** (stricter than geodesic-sealer optional GET) |
| Subprocess / shell | **None** |
| Filesystem write | Only `--write` with `--i-consent` |
| Publish | **None** |

## Epistemic limits

- Software P6 attestation ≠ TPM / hardware root of trust  
- Local Merkle gossip leaf ≠ live SLM network consensus  
- Non-collapsing receipt is a **policy invariant**, not a physics claim  

## Operator rules

- Do not store secrets in `--truth` / `--chaos` / `--anchor-file`  
- Prefer Continuum capsules for consequential claims  
- Human remains the publisher  

## Proof

```bash
python scripts/self_check.py
```
