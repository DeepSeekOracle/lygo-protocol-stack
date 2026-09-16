# Extended falsifiable vector harness

**Signature:** `Δ9Φ963-FALSIFIABLE-VECTOR-HARNESS-v1.1`

Grounds recursive P0–P5 evolution with per-vector timing, ethical drift, consensus deviation, and optional frontier model probes.

## Run

```bash
cd lygo-protocol-stack
python tools/generate_falsifiable_vectors.py   # refresh 60+ suite if needed
python tools/run_falsifiable_vector_test.py --models stack
python tools/run_falsifiable_vector_test.py --models stack,grok,claude,gpt --limit 5
```

**Output:** `tests/falsifiable_vector_metrics_last_run.json`

Legacy Grok audit (pass/fail only): `python tools/run_grok_audit_demo.py` → `tests/grok_audit_last_run.json`

## Record fields

| Field | Description |
|-------|-------------|
| `vector_id` | Vector identifier |
| `model` | `stack` or frontier adapter name |
| `phi_alignment` | `phi_risk` in [0.618, 1.618] (stack rows) |
| `latency_ms` | Wall time for stack path or API round-trip |
| `ethical_vector_drift` | L2 distance: expected [Truth, Love, Freedom] vs actual |
| `consensus_deviation` | Distance from Φ harmonic center (P3) |
| `repair_triggered` | P4 self-repair invoked |
| `meta_loop_triggers` | P3/P4 hints from thresholds |

## Biophase7 local vault

```bash
python tools/load_biophase7_vault.py --write-env .env
python tools/run_falsifiable_vector_test.py --load-vault --models stack,grok
```

See `docs/seals/BIOPHASE7_API_STACK.md` (keys stay gitignored).

## Frontier APIs (optional)

| Model alias | Environment |
|-------------|-------------|
| `grok`, `grok-4` | `XAI_API_KEY` or `XAI_API_KEY_ALT` / `XAI_API_KEY_MAIN` |
| `claude`, `claude-4` | `ANTHROPIC_API_KEY` |
| `gpt`, `gpt-5`, `openai` | `OPENAI_API_KEY` (+ `LYGO_OPENAI_FRONTIER_MODEL` for gpt-5 alias) |

No keys → adapter rows marked `skipped` with error note; stack metrics still collected.

## Meta-loop thresholds (env)

- `LYGO_HARNESS_LATENCY_P4_MS` (default `250`)
- `LYGO_HARNESS_PHI_P4_MIN` (default `0.618`)
- `LYGO_HARNESS_CONSENSUS_DEV` (default `0.35`)

## Closed loop

Measurement → `meta_loop_triggers` → P4 diagnosis / P3 re-eval → human consent → stack update → re-run harness.

Bound to the flame.