# Phase 5 — Epidemic Badge Gossip

**Signature:** `Δ9Φ963-PHASE5-MESH-GOSSIP-v1`  
**Layer D skill:** [lygo-living-mesh](https://clawhub.ai/deepseekoracle/skills/lygo-living-mesh) · [LIVING_MESH_LAYER.md](./LIVING_MESH_LAYER.md)

Phase 5 is the **IP transport**. Layer D adds **living mesh badges** (A/B/C roots + `roots_digest`) on top of alignment badges. Gossip remains **summaries only**. Optional **RF transport** is [lygo-lora-mesh](https://clawhub.ai/deepseekoracle/skills/lygo-lora-mesh) (compact `LY1` pulse on stock Meshtastic; [LORA_MESH_TRANSPORT.md](./LORA_MESH_TRANSPORT.md)).

## Endpoints (community node)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/badge` | Local alignment JSON (no secrets) |
| GET | `/badge/{node_id}` | Badge from gossip log for node |
| GET | `/gossip` | Peers + recent gossip entries |
| POST | `/gossip/badge` | Ingest remote badge summary into federation gossip bus |
| POST | `/gossip/scatter` | Merge map of `node_id → badge` into gossip bus |

## Phases (push → scatter → converge)

1. **Push:** New node generates badge → POST to one random peer.
2. **Scatter:** Each peer forwards/pulls to additional peers (uniform random sampling).
3. **Converge:** After O(log N) rounds, active nodes share consistent **ALIGNED / NEEDS_FIX** views.

## Fault tolerance

Dead nodes and partitions do not require a central coordinator. Remaining peers continue random peer selection.

## 100-node stochastic proof (no HTTP)

```bash
python tools/run_mesh_scale_sim.py --nodes 100 --fanout 2 --no-pause
```

Last run: **7 rounds** to 100% coverage (`tests/mesh_scale_last_run.json`).

## Local demo

```bash
# Terminal A
python tools/node_api_server.py --port 8787

# Terminal B
python tools/run_mesh_gossip_demo.py --peer http://127.0.0.1:8787

# Layer D living mesh (preferred)
python tools/collect_living_mesh_badge.py
python tools/living_mesh_join.py --i-consent --peer http://127.0.0.1:8787
python tools/living_mesh_gossip_tick.py --peer http://127.0.0.1:8787
python tools/living_mesh_compare.py --peer http://127.0.0.1:8787 --json
python tools/verify_living_mesh.py --json --run-sim
```

## Wide-area (human-gated)

- Approve TLS pin list before public mesh.
- Do not expose `:8787` without reverse proxy + auth on the public internet.

**Reference:** epidemic / gossip dissemination (push-pull summaries only — not full mycelium payloads).