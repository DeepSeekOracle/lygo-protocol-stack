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