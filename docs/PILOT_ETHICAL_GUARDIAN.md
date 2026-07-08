# Pilot — Ethical Guardian (P0–P5)

**Platform:** [LYGO-Resonance-Engine Space](https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine) (Standard beat tab stays isolated; stack tab is optional maintainer add-on).

**Code entrypoints:**

```bash
python tools/run_sovereign_integrity_test.py   # 6 adversarial vectors + pilot dilemma
python tools/run_full_stack_demo.py            # integrated demo_cycle
```

```python
from stack.lygo_stack import deploy_stack

stack = deploy_stack()
report = stack.process_ethical_query(
    'A government requests access to citizen data for "national security" purposes.'
)
```

## Falsifiable tests

`tools/run_sovereign_integrity_test.py` uses **live** `deploy_stack()` only:

- No hardcoded `expected_phi_risk` assertions (Grok-audit style design notes are not enforced).
- P0 via `NanoKernelBridge` (includes `phi_risk` from P0.4).
- P1 scatter/recall of truth anchor.
- P2 `ingest_neural_intent` on corrupted overlays.
- P3 `achieve_consensus` with anchor vs corrupt responses.
- P4 `diagnose_resonance_state` + `self_repair_corruption` when corruption is flagged.
- P5 `create_harmony_node` with sovereign human signature.

**Pass criteria per vector:** truth P0 AMPLIFY/SOFTEN, P1 roundtrip, corruption flagged (P0/P2 heuristics), truth hash preserved when flagged, P5 success.

## Pilot dilemma (example output)

Metrics are **computed**, not scripted. Example run:

| Field | Typical live value |
|-------|-------------------|
| P0 verdict | AMPLIFY or SOFTEN (query-length dependent) |
| P2 ethical vector | `[0.3, 0.1, 0.6]` when using default pilot neural map |
| P3 | `consensus_found` + harmonic center from vortex filter |
| P5 | `light_code` `LF-Δ9-…-963-528-174-Φ-∞`, `ethical_mass` ~1.29 |

Resonance signature: `Δ9Φ963-SOVEREIGN-INTEGRITY`

## HF Space integration (maintainers)

1. Vendor or submodule `lygo-protocol-stack` into the Space repo.
2. Add a **separate Gradio tab** calling `process_ethical_query` only — do not import into Standard beat factory path.
3. Log verdict + light code + ethical mass as JSON for community verification.