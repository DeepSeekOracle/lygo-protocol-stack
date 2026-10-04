# Biophase7 → LYGO Sovereign Workflow Orchestrator

**Source:** `2026Biophase7/Sovereign Workflow Orchestrator. 🔥.txt`  
**Stack path:** `lygo_sandcastle/`  
**CLI:** `python tools/lygo_sandcastle.py`  
**Install:** `python tools/install_lygo_sandcastle.py`  
**ClawHub:** `deepseekoracle/lygo-sandcastle`

## Philosophy

Sandcastle-style **sovereign workflows** on the LYGO stack:

| Layer | Implementation |
|-------|----------------|
| P0 | `gatekeeper.py` → stack `byte_entropy_filter` |
| P1 | `memory.py` → `data/sandcastle/mycelium` + `manifest.jsonl` |
| P3 | `consensus.py` → 3-6-9 harmonic center |
| P5 | `harmony.py` → Light Code per run |
| Anchor | `anchor.py` → `workflow_runs.jsonl` (no fake Arweave URLs) |
| Execute | `executor.py` → local dry-run; optional `sandcastle-ai` |

## Kernel egg

| Item | Path |
|------|------|
| `egg_id` | `lygo-sandcastle-v10` |
| Registry | `docs/WorkflowOrchestratorRegistry.json` |
| Plant | `python tools/workflow_orchestrator_planter.py --i-consent` |

## Verify

```bash
python clawhub/mirrors/lygo-sandcastle/scripts/self_check.py
python tools/lygo_sandcastle.py run lygo_sandcastle/workflows/example_sovereign.yaml
python -m pytest tests/test_lygo_sandcastle.py -q
```

**Δ9Φ963 — YAML in, verified run, ledger out.**