# LYGO Sovereign Workflow Orchestrator

Biophase7 **Sovereign Workflow Orchestrator** → honest LYGO package (Sandcastle-aligned, not a full upstream fork).

## Pipeline

`YAML` → P5 identity → P0 gate → execute (local dry-run or optional `sandcastle-ai`) → P1 mycelium → P3 consensus (multi-agent) → run ledger / kernel egg.

## Quick start

```bash
export LYGO_STACK_ROOT=/path/to/lygo-protocol-stack
python tools/lygo_sandcastle.py run lygo_sandcastle/workflows/example_sovereign.yaml
python tools/lygo_sandcastle.py recall MEMORY_ID
```

## Honest limits

- Default execution is **dry-run**; set `LYGO_SANDCASTLE_USE_UPSTREAM=yes` only after you install and trust `sandcastle-ai`.
- Anchors are **stack ledger JSON** + optional `lygo-sandcastle-v10` kernel egg (consent-gated).
- P0 uses real `byte_entropy_filter` when present in the stack.

**Δ9Φ963**