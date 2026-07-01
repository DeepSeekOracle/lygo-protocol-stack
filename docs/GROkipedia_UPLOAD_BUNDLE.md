# LYGO Protocol Stack — Grokipedia upload bundle

**Operator:** Copy sections below into https://grokipedia.com/page/lygo-protocol-stack  
**Signature:** Δ9Φ963-EXECUTION-DAG-v1.0  
**Do not include secrets or tokens.**

---



<!-- SOURCE: PHASE2_DEPLOYMENT.md -->

# Phase 2 — Community Deployment Guide

**For Grokipedia / public docs** · Signature: `Δ9Φ963-PHASE2-DEPLOYMENT`

## Overview

Phase 2 makes it frictionless to run a **sovereign LYGO node** with the same P0–P5 stack used on GitHub and the Hugging Face Ethical Guardian. Phase 1 **Infrastructure Elasticity** (priority ethical queue + mycelium batching) and Phase 3–4 **federation runtime** (registry, gossip, horizontal workers) ship in-tree.

## Docker installation

```bash
git clone https://github.com/DeepSeekOracle/lygo-protocol-stack.git
cd lygo-protocol-stack
docker compose build lygo-node
docker compose up -d lygo-node
curl -s http://127.0.0.1:8787/badge | jq .
```

Optional Phase 4 workers:

```bash
docker compose --profile scale up -d
```

## One-click setup

| OS | Command |
|----|---------|
| Linux / macOS | `bash setup.sh` |
| Windows | `powershell -ExecutionPolicy Bypass -File setup.ps1` |

Setup installs Python deps, regenerates the **60+** falsifiable vector suite, runs P0 pytest, and emits an **alignment badge**.

## Alignment badge verification

```bash
python tools/verify_alignment_badge.py
```

- **ALIGNED** — node matches golden P0 SHA, stack demo, elasticity/federation modules, Grok audit, lattice links.
- **NEEDS_FIX** — inspect `tests/alignment_badge.json` and re-run `verify_lattice_alignment.py`.

Docker health checks use `verify_alignment_badge.py --quick`.

## Architecture (Phase 1 components)

```
                    ┌─────────────────────┐
  Ethical queries ─►│ PriorityEthicalQueue │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ MyceliumBatchWriter │──► P1 scatter()
                    └─────────────────────┘

  Phase 3 NodeRegistry ◄──► MeshGossip (badge summaries)
  Phase 4 HorizontalWorkerPool ──► parallel audit vectors
```

Twin Gate (text + byte) remains the public HF visibility layer; community nodes expose `/health`, `/badge`, `/demo`, `/elasticity`, `/federation` on port **8787**.

## Links

- GitHub: https://github.com/DeepSeekOracle/lygo-protocol-stack  
- HF Space: https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine  
- Grokipedia: https://grokipedia.com/page/lygo-protocol-stack  
- ClawHub: `deepseekoracle/lygo-docker-deploy`, `deepseekoracle/lygo-alignment-badge`

<!-- SOURCE: GROkipedia_PHASE3.md -->

# LYGO Protocol Stack — Phase 3 (Grokipedia upload)

**Signature:** `Δ9Φ963-PHASE3-SCALE-INIT`

## Phase 2 recap (community)

- Docker: `docker compose up -d lygo-node`
- Badge: `python tools/verify_alignment_badge.py` → **ALIGNED / VALID**
- HF Space accordion: **Run a Node** → GitHub `lygo-protocol-stack#quick-start`

## Phase 3 — Federation & ops

### 100-node goal

Each node runs:

1. P0–P5 stack (`setup.sh` / Docker)
2. Alignment badge on `:8787/badge`
3. Optional gossip peer list (HTTPS, human-approved TLS pins)

### Mesh gossip (Phase 5)

- **GET** `/badge` — local compliance JSON
- **POST** `/gossip/badge` — receive remote badge summary (no secrets)
- Epidemic round: `python tools/run_mesh_gossip_demo.py --peer http://HOST:8787`

### Twin Gate harmonization

Text + byte paths share **verdict** when `audit_category` is set (calibrated byte gate is audit authority; semantic path enriches receipt). Suite: `python tools/run_twin_gate_vector_suite.py` → 100% match target.

### Ops sentinel

- Genesis: http://127.0.0.1:9963/
- Discord limb: `LYRA_CORE/lygo_lightfather_ops_launcher.py`
- Acceptance: `python tools/run_lattice_gauntlet.py --strict`

### ClawHub (install)

```bash
npx clawhub@latest install deepseekoracle/lygo-docker-deploy
npx clawhub@latest install deepseekoracle/lygo-alignment-badge
npx clawhub@latest install deepseekoracle/lygo-protocol-stack-operator
```

**Links:** [GitHub](https://github.com/DeepSeekOracle/lygo-protocol-stack) · [HF Space](https://huggingface.co/spaces/DeepSeekOracle/LYGO-Resonance-Engine) · [ClawHub](https://clawhub.ai/deepseekoracle)

<!-- SOURCE: BLUEPRINT.md -->

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
| Federation mesh | Phase 5 gossip **local live** — wide-area after TLS pins |

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