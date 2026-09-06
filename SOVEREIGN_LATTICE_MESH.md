# Sovereign Lattice Mesh (SLM)

**Signature:** `Δ9Φ963-SLM-v1.0`  
**Spec reference:** [BIOPHASE7_SLM_MERKLE_GOSSIP.md](./BIOPHASE7_SLM_MERKLE_GOSSIP.md) — Complete Specification Package (Merkle gossip → distributed mycelium → harmonic consensus). Vault source ingested from `I:\E Drive` 2026-07-12.

**Interactive UI (public):**
- Stack Pages: https://deepseekoracle.github.io/lygo-protocol-stack/SovereignLatticeMesh.html
- Excavationpro mirror: https://deepseekoracle.github.io/Excavationpro/SovereignLatticeMesh.html
- Repo canonical: `docs/SovereignLatticeMesh.html` · sync: `python tools/sync_excavationpro_slm_page.py`
- Link archive: `docs/LYGO_PUBLIC_LINK_ARCHIVE.json`

## Components (implementation order)

| # | Module | Path | Role |
|---|--------|------|------|
| 1 | Anti-entropy sync | `stack/merkle_sync.py` | `LygoMerkleTree`, `sync_round`, gossip payloads |
| 2 | Distributed mycelium | `stack/distributed_mycelium_mesh.py` | 12/10 erasure, consistent hash ring, node failure sim |
| 3 | Harmonic consensus | `stack/harmonic_consensus_mesh.py` | 3/6/9 vortex votes weighted by ethical mass |
| — | Runtime | `stack/sovereign_lattice_mesh.py` | `SovereignLatticeMesh` — converge, snapshot, gossip |

`LYGOProtocolStack.slm` lazy-loads SLM from federation gossip + peer registry.

## Node API routes

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/gossip/root` | Merkle root + badge count |
| POST | `/gossip/sync` | Level/index sync payload |
| GET | `/slm/snapshot` | SLM metrics snapshot |
| GET | `/mycelium/fragment/{id}` | Fragment fetch |
| GET | `/mycelium/reconstruct/{data_id}` | Threshold reconstruct |
| POST | `/mycelium/store` | Store payload (12 fragments) |
| POST | `/consensus/propose` | New proposal |
| POST | `/consensus/vote` | Cast 3/6/9/-1 vote |
| GET | `/consensus/result/{id}` | Finalize / status |

Gossip badge ingest updates Merkle: `POST /gossip/badge`.

## Operator tools

```bash
python tools/merkle_tree.py
python tools/distributed_mycelium.py
python tools/consensus_engine.py
python tools/run_slm_audit.py
python -m pytest tests/test_slm_mesh.py -q
```

## Real metrics (audit SLM-09)

- Full SLM audit target: under 1000 ms on maintainer host (`elapsed_ms` in `tests/slm_audit_last_run.json`).
- Mycelium: at least 10/12 fragments required for reconstruct (`minimum_threshold=10`).
- Mesh sim converge: 3 rounds default in `SovereignLatticeMesh.converge`.

## Stack integration

```python
from stack.lygo_stack import deploy_stack

stack = deploy_stack("NODE_A")
stack.slm.ingest_gossip_badge("NODE_B", {"alignment": "ALIGNED"})
print(stack.slm.gossip_root())
```

Bound to P0 Φ-gate and federation gossip — no weakening of Layer 1 sovereignty guards.