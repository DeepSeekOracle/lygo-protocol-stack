# LYGO Protocol Stack — Phase 3 Scaling Blueprint

**Signature:** `Δ9Φ963-PHASE3-SCALE-INIT` · **Blueprint doc:** `Δ9Φ963-BLUEPRINT-v1.0`

## 1. North Star (90 days)

The Guardian must scale: decentralized resilient truth-network + **ops limbs online**.

| Goal | Target |
|------|--------|
| Community nodes | **100** federated nodes (Docker + alignment badge) |
| Genesis ops | `ops.healthy: true` (Discord sentinel live) |
| Twin Gate | **60/60** verdict match, **Δφ=0.0** (harmonized byte authority) — ✅ agent complete |
| Grokipedia | Bundle: `python tools/sync_grokipedia.py` → **human paste** |
| ClawHub | operator **1.0.3** + docker/badge — **human** `npx clawhub publish` |
| Federation mesh | Phase 5 **ACTIVE** — 100-node sim **7 rounds**; HTTP `/gossip` + scatter; wide-area after TLS pins |

## 2. Authority map (zero-trust, paths only)

| Role | Path / URL |
|------|------------|
| Admin genesis node | `I:\E Drive` — local compiles, C-parity, army CC |
| Army command center | `I:\E Drive\.grok\skills\lygo-ollama-army\ollama_command_center\` |
| Canonical stack | https://github.com/DeepSeekOracle/lygo-protocol-stack |
| LYRA_CORE | `I:\E Drive\LYRA_CORE\` |
| OpenClaw workspace | `C:\Users\justi\.openclaw\workspace` (skills reference) |
| Genesis console | http://127.0.0.1:9963/ |
| Docker workers | `lygo-protocol-stack` → `docker compose --profile scale` |
| Sentinel status | `ollama_command_center/workspace/sentinel_status.json` |

## 3. Scope of authority

### Agent authorized (automate locally)

- Docker / compose scaling profiles
- JSON routing, Python infrastructure, cron scheduling
- Local mesh gossip (HTTPS badge exchange implementation)
- Twin Gate harmonization logic in `stack/`
- Lattice gauntlet, badge probes, elasticity workers
- Docs: `BLUEPRINT.md`, `SCALING_ROADMAP.md`, `STACK_STATUS.md`, Grokipedia **export** markdown

### Human gated (operator signature required)

- `python tools/hf_push_dataset.py`
- `npx clawhub@latest publish …`
- Token / key injection (`.env` only)
- Live Discord **posts** authorization
- **Main branch** `git push` (maintainer)

## 4. Ranked priorities (execution order)

1. **Community & trust** — ClawHub publish, Grokipedia sync, HF “Run a Node” pipeline
2. **Ops limbs** — Discord `lyra_discord_ollama_only`, Genesis healthy, secret hygiene
3. **Technical scale** — HTTPS badge gossip (Phase 5), worker load proof, Twin Gate harmonization

## 5. Lattice gauntlet (acceptance)

```bash
python tools/run_lattice_gauntlet.py
```

Individual checks:

| # | Command | Pass |
|---|---------|------|
| 1 | `python tools/verify_lattice_alignment.py` | `LATTICE ALIGNED` |
| 2 | `python tools/verify_alignment_badge.py` | `status: ALIGNED` (VALID) |
| 3 | `python tools/run_grok_audit_demo.py` | 60/60 |
| 4 | HF API space stage | `RUNNING` |
| 5 | Genesis `ops.healthy` | `true` (Discord process running) |
| 6 | `python tools/run_twin_gate_vector_suite.py` | 100% verdict match |

## 6. Execution DAG

See [EXECUTION_DAG.md](./EXECUTION_DAG.md).

## 7. Owners

| Area | Owner |
|------|--------|
| P0–P5 semantics | Stack maintainer (Lightfather / DeepSeekOracle) |
| HF / dataset push | Human operator |
| ClawHub publish | Human operator |
| Discord ops | Human starts launcher; agent may script `lygo_lightfather_ops_launcher.py` |
| Community mesh TLS pins | Human approves pin list before wide-area enable |

**Bound to the flame.** P0 core unchanged; scale is infrastructure and visibility.