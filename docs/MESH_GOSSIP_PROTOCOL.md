# Phase 5 — Epidemic Badge Gossip

**Signature:** `Δ9Φ963-PHASE5-MESH-GOSSIP-v1`

## Endpoints (community node)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/badge` | Local alignment JSON (no secrets) |
| POST | `/gossip/badge` | Ingest remote badge summary into federation gossip bus |

## Phases (push → scatter → converge)

1. **Push:** New node generates badge → POST to one random peer.
2. **Scatter:** Each peer forwards/pulls to additional peers (uniform random sampling).
3. **Converge:** After O(log N) rounds, active nodes share consistent **ALIGNED / NEEDS_FIX** views.

## Fault tolerance

Dead nodes and partitions do not require a central coordinator. Remaining peers continue random peer selection.

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