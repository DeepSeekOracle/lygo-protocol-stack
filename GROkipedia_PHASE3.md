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