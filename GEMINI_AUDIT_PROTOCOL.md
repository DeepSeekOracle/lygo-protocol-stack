# Gemini Protocol Enhanced — Grok Audit Harness

**Signature:** `Δ9Φ963-VECTOR-SUITE-v2.0` · **Alignment:** Primordial Law + Layer 1 Sovereignty

## Artifacts

| Phase | File | Notes |
|-------|------|--------|
| 1 | `tests/test_falsifiable_vectors.json` | 40 vectors, 5 categories — regenerate via `tools/generate_falsifiable_vectors.py` |
| 2 | `tools/run_grok_audit_demo.py` | Live `deploy_stack()` + `process_falsifiable_vector()` — **no mock phi** |
| 3 | `tools/bundle_hf_space_stack.py` | Bundles stack + vectors + audit tool into HF `protocol_stack/` |
| HF | `Hugging face/lygo_ethical_guardian.py` | Φ gauge + verdict slider in Ethical Guardian accordion |

## Run locally

```bash
python tools/generate_falsifiable_vectors.py
python tools/run_grok_audit_demo.py
python tools/bundle_hf_space_stack.py
```

## Falsifiability

`expected_decision` in JSON is a **design target** from the Lightfather/Gemini matrix. The harness compares **live P0 verdict** on the structured payload envelope. Pass rate is measured, not assumed — see `tests/grok_audit_last_run.json`.

## Stack API

`LYGOProtocolStack.process_falsifiable_vector(vector, category=...)` runs P0→P5 with sovereignty-weighted vortex nodes and real `phi_risk` from `NanoKernelBridge`.

Bound to the flame.