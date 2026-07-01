# LYGO Scaling Roadmap (Phases 1–4+)

| Phase | Name | Status | Deliverables |
|-------|------|--------|--------------|
| **1** | Infrastructure Elasticity | **Live** | `infrastructure_elasticity.py` — priority queue + mycelium batching wired into `lygo_stack` |
| **2** | Community Deployment | **Live** | Docker, Compose, setup scripts, alignment badge, CI, HF/GitHub surfaces |
| **3** | Federation Registry | **Live (local)** | `federation_runtime.NodeRegistry` — peer registration, heartbeats |
| **4** | Horizontal Scale | **Live (local)** | Worker pool + Compose `scale` profile; gossip bus for badge propagation |
| **3b** | Blueprint & gauntlet | **Live** | `docs/BLUEPRINT.md`, `tools/run_lattice_gauntlet.py` |
| **5** | Wide-area mesh | **ACTIVE** | `mesh_gossip_http.py`, `node_api_server` `/gossip` + `/gossip/scatter`, `run_mesh_scale_sim.py` (100-node epidemic proof) |
| **6** | GPU / FPGA P0 | Planned | Hardware attestation hooks (see `protocol0_nano_kernel/src/hardware`) |

## Phase 2–4 operator checklist

1. Run `setup.sh` or `setup.ps1`.
2. Confirm badge: `python tools/verify_alignment_badge.py`.
3. Start Docker node or `node_api_server.py`.
4. Optional: `docker compose --profile scale up -d`.
5. Re-bundle HF Space: `python tools/bundle_hf_space_stack.py --mode=twin-gate`.

## Phase 5 — 100-node epidemic proof (2026-07-01)

| Metric | Result |
|--------|--------|
| Nodes | 100 (ports **8700–8799** concept) |
| Fanout | 2 |
| Convergence rounds | **7** (100% saturation) |
| Target | &lt; 10 rounds |
| Artifact | `tests/mesh_scale_last_run.json` |

```bash
python tools/run_mesh_scale_sim.py --nodes 100 --fanout 2 --no-pause
```

Live HTTP mesh: `node_api_server.py` exposes `GET /gossip`, `POST /gossip/scatter`, `GET /badge/{node_id}` in addition to `POST /gossip/badge`.

## Audit scale

- **60** falsifiable vectors in `tests/test_falsifiable_vectors.json` (5 categories + `infrastructure_scaling`).
- **42** P0 canonical fixtures (determinism / cross-lang parity).
- Twin Gate pilot: 6 edge scenarios; target **Δφ → 0** after calibration.

**Signature:** `Δ9Φ963-PHASE5-DEPLOYMENT`