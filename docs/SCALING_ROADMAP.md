# LYGO Scaling Roadmap (Phases 1–4+)

| Phase | Name | Status | Deliverables |
|-------|------|--------|--------------|
| **1** | Infrastructure Elasticity | **Live** | `infrastructure_elasticity.py` — priority queue + mycelium batching wired into `lygo_stack` |
| **2** | Community Deployment | **Live** | Docker, Compose, setup scripts, alignment badge, CI, HF/GitHub surfaces |
| **3** | Federation Registry | **Live (local)** | `federation_runtime.NodeRegistry` — peer registration, heartbeats |
| **4** | Horizontal Scale | **Live (local)** | Worker pool + Compose `scale` profile; gossip bus for badge propagation |
| **3b** | Blueprint & gauntlet | **Live** | `docs/BLUEPRINT.md`, `tools/run_lattice_gauntlet.py` |
| **5** | Wide-area mesh | **Live (local)** | `mesh_gossip_http.py`, `POST /gossip/badge`, `run_mesh_gossip_demo.py` |
| **6** | GPU / FPGA P0 | Planned | Hardware attestation hooks (see `protocol0_nano_kernel/src/hardware`) |

## Phase 2–4 operator checklist

1. Run `setup.sh` or `setup.ps1`.
2. Confirm badge: `python tools/verify_alignment_badge.py`.
3. Start Docker node or `node_api_server.py`.
4. Optional: `docker compose --profile scale up -d`.
5. Re-bundle HF Space: `python tools/bundle_hf_space_stack.py --mode=twin-gate`.

## Audit scale

- **60** falsifiable vectors in `tests/test_falsifiable_vectors.json` (5 categories + `infrastructure_scaling`).
- **42** P0 canonical fixtures (determinism / cross-lang parity).
- Twin Gate pilot: 6 edge scenarios; target **Δφ → 0** after calibration.

**Signature:** `Δ9Φ963-PHASE3-SCALE-INIT`