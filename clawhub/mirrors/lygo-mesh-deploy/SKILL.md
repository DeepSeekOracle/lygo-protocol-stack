---
name: lygo-mesh-deploy
description: Phase 5 LYGO federation mesh — deploy local node cluster, monitor HTTP gossip epidemic convergence, stochastic 100-node scale proof. Ports 8700+, GET/POST /gossip endpoints.
metadata: {"lygo": true, "stack": true, "phase": 5, "version": "1.0.0", "github": "https://github.com/DeepSeekOracle/lygo-protocol-stack", "pages": "https://deepseekoracle.github.io/lygo-protocol-stack/", "signature": "Δ9Φ963-PHASE5-LIVE-DEPLOYMENT"}
---

# lygo-mesh-deploy

**Phase 5** wide-area mesh tooling (local HTTP proof before TLS wide-area).

## When to use

- Prove epidemic badge gossip converges in **&lt;20 rounds** (live) or **&lt;10 rounds** (sim).
- Operate community mesh alongside Docker `lygo-node` on **8787**.

## Commands

```bash
git clone https://github.com/DeepSeekOracle/lygo-protocol-stack.git
cd lygo-protocol-stack

# Stochastic proof (100 nodes, no HTTP)
python tools/run_mesh_scale_sim.py --nodes 100 --fanout 2 --no-pause

# Live HTTP cluster (Linux/macOS)
./tools/deploy_100_nodes.sh
python tools/monitor_convergence.py --nodes 100 --wait-health 180
python tools/deploy_mesh_cluster.py stop

# Windows
pwsh tools/deploy_100_nodes.ps1
python tools/monitor_convergence.py
```

## Node API (per peer)

| Method | Path |
|--------|------|
| GET | `/badge`, `/gossip`, `/health` |
| POST | `/gossip/badge`, `/gossip/scatter` |

## Safety

- Do not expose gossip ports on the public internet without TLS pins and user approval.
- No autonomous wide-area deploy without explicit operator sign-off.

**Install:** `npx clawhub@latest install deepseekoracle/lygo-mesh-deploy`