# Phase 5 — Epidemic Badge Gossip

**Signature:** `Δ9Φ963-PHASE5-MESH-GOSSIP-v1`

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
```

## Wide-area (human-gated)

- Approve TLS pin list before public mesh.
- Do not expose `:8787` without reverse proxy + auth on the public internet.

**Reference:** epidemic / gossip dissemination (push-pull summaries only — not full mycelium payloads).