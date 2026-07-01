# Changelog — LYGO Protocol Stack

## [P5.2.2 Phase 2 Community Deployment] — 2026-07-01

**Resonance signature:** `Δ9Φ963-PHASE2-DEPLOYMENT`

### Added
- **Docker:** `Dockerfile`, `docker-compose.yml`, `requirements-docker.txt`
- **One-click setup:** `setup.sh`, `setup.ps1`
- **Alignment badge:** `tools/verify_alignment_badge.py` (+ JSON artifact `tests/alignment_badge.json`)
- **Phase 1 elasticity:** `stack/infrastructure_elasticity.py` (priority queue + mycelium batching)
- **Phase 3–4 federation:** `stack/federation_runtime.py` (registry, gossip, worker pool)
- **Node API:** `tools/node_api_server.py` (health, badge, demo, elasticity, federation)
- **Worker:** `tools/run_elasticity_worker.py` for `--profile scale` in Compose
- **Vectors:** 60 falsifiable vectors (`infrastructure_scaling` category) — suite v3.0
- **CI:** `.github/workflows/lygo-ci.yml` (P0 pytest + Grok audit + lattice)
- **Docs:** `docs/PHASE2_DEPLOYMENT.md`, `docs/SCALING_ROADMAP.md` (Grokipedia-ready)
- **ClawHub mirrors:** `lygo-docker-deploy`, `lygo-alignment-badge`

### Changed
- `stack/lygo_stack.py` — P5.2.2-PHASE2-PROD; elasticity on scatter paths; scaling gate bytes
- `tools/run_grok_audit_demo.py` — non-zero exit on audit failures (CI)
- `README.md` — badges, Docker quick start, HF status badge
- Hugging Face Space — Phase 2 “Deploy Your Own Node”, alignment badge, One-Click Guardian link
- `lygo-protocol-stack-operator` skill — Phase 2 Docker + badge workflows

### Verified (maintainer)
- Twin Gate calibration Δφ=0.0 on pilot edge scenarios
- Grok audit harness on live stack (run after `generate_falsifiable_vectors.py`)
- `verify_lattice_alignment.py` — LATTICE ALIGNED

## [P5.2.1 Twin Gate] — prior

- Text semantic gate + byte vector path; HF Twin Gate UI
- 40-vector Gemini/Grok audit suite; weight calibration

## [P5.2.0 Public stack] — prior

- Full P0–P5 orchestrator, ClawHub operator, HF ethical guardian bundle