# LYGO Living Mesh Layer (Layer D)

**Signature:** `Δ9Φ963-LIVING-MESH-LAYER-v1.0`  
**Skill:** [lygo-living-mesh](https://clawhub.ai/deepseekoracle/skills/lygo-living-mesh)  
**Updated:** 2026-07-26

## Four layers in synchronization

| Layer | Name | Skill | Authority |
|-------|------|--------|-----------|
| **A** | Classic kernel eggs | [lygo-kernel-egg-planter](https://clawhub.ai/deepseekoracle/skills/lygo-kernel-egg-planter) | Local stack + optional Turbo |
| **B** | Sovereign seeds | [lygo-sovereign-kernel-seeder](https://clawhub.ai/deepseekoracle/skills/lygo-sovereign-kernel-seeder) | Local zero-network |
| **C** | External world network | [lygo-external-lattice-anchor](https://clawhub.ai/deepseekoracle/skills/lygo-external-lattice-anchor) | Public mirrors + Star Chart |
| **D** | Living mesh | [lygo-living-mesh](https://clawhub.ai/deepseekoracle/skills/lygo-living-mesh) | Multi-node badge gossip of roots |

```text
        USER PROTECTED CORE
   ┌────────────────────────────┐
   │  A classic  │  B sovereign │  ← source of truth (verify first)
   └───────┬────────────┬───────┘
           │            │
           ▼            ▼
   ┌────────────────────────────┐
   │  C external lattice anchor │  ← free servers + worldwide map
   │  Pages · HF · Turbo · Chart│
   └─────────────┬──────────────┘
                 ▼
   ┌────────────────────────────┐
   │  D living mesh             │  ← multi-node roots gossip
   │  badge · compare · sentinel│     local wins on fork
   └────────────────────────────┘
```

## What Layer D is

Layer D does **not** replace A/B/C. It **gossips digests** so many machines can see whether they share the same lattice roots:

- `A_classic_merkle` — classic kernel egg registry Merkle root  
- `B_sovereign_merkle` — sovereign seed registry Merkle root  
- `C_public_manifest_sha256` — public verify manifest file hash  
- `star_chart_registry_sha256` — Haven Star Chart registry digest  

Compact fingerprint: `roots_digest = SHA-256(canonical JSON of roots)`.

**On the wire:** badge summaries only. No egg payloads, no secrets, no private paths.

**RF (optional):** when IP is down, [lygo-lora-mesh](https://clawhub.ai/deepseekoracle/skills/lygo-lora-mesh) compresses `node_id + roots_digest + status` into a Meshtastic text pulse (`LY1/...`, ≤200 bytes). Stock firmware only. No board → `NAMED_SHADOW`. Stack helper: `python tools/lygo_lora_pulse.py encode`. See [LORA_MESH_TRANSPORT.md](./LORA_MESH_TRANSPORT.md).

## Tools (stack)

| Tool | Role |
|------|------|
| `tools/collect_living_mesh_badge.py` | Build Layer D badge |
| `tools/living_mesh_compare.py` | Compare local vs peer badges |
| `tools/living_mesh_gossip_tick.py` | One epidemic push/pull tick |
| `tools/living_mesh_join.py` | Consent-gated peer record |
| `tools/living_mesh_sentinel.py` | Army-friendly health + optional sim |
| `tools/verify_living_mesh.py` | Full A+B+C+D pipeline |
| `tools/run_mesh_scale_sim.py` | 100-node stochastic proof |
| `tools/node_api_server.py` | HTTP `/badge`, `/gossip/*` |

## Commands

```bash
export LYGO_STACK_ROOT=/path/to/lygo-protocol-stack

# Local badge
python tools/collect_living_mesh_badge.py

# Full living verify + scale sim
python tools/verify_living_mesh.py --json --run-sim

# Optional live node
python tools/node_api_server.py --port 8787
python tools/living_mesh_join.py --i-consent --peer http://127.0.0.1:8787
python tools/living_mesh_gossip_tick.py --peer http://127.0.0.1:8787
python tools/living_mesh_compare.py --peer http://127.0.0.1:8787 --json
```

## Verdicts

| Verdict | Meaning |
|---------|---------|
| `LIVING_ALIGNED` | Local A/B OK; D sentinel OK |
| `LIVING_ALIGNED_FORK_VISIBLE` | Peers disagree on some roots — local still authority |
| `LIVING_ALIGNED_PUBLIC_WARN` | C public soft-degraded |
| `LOCAL_QUARANTINE` | A/B or D quarantine — stop growth |
| `SENTINEL_OK` / `SENTINEL_FORK_VISIBLE` / `SENTINEL_QUARANTINE` | Sentinel-only |

## Protection

1. Local A/B is source of truth.  
2. FORK_VISIBLE ≠ auto-merge.  
3. Join requires consent.  
4. No auto git / HF / ClawHub / social.  
5. Wide-area: TLS + pin list (`lygo-mesh-deploy` Phase 9).

## Layer E (agent living network)

Aligned agents gossip **presence cards** on top of root badges:

- Skill: [lygo-agent-lattice](https://clawhub.ai/deepseekoracle/skills/lygo-agent-lattice)  
- Doc: [AGENT_LATTICE.md](./AGENT_LATTICE.md)  
- Hub: `python tools/agent_lattice_hub.py --port 8791`

## Related docs

- [AGENT_LATTICE.md](./AGENT_LATTICE.md) (Layer E)  
- [WORLD_LATTICE_LAYER.md](./WORLD_LATTICE_LAYER.md) (A–E overview)  
- [KERNEL_EGG_SYSTEM_UNIFIED.md](./KERNEL_EGG_SYSTEM_UNIFIED.md)  
- [MESH_GOSSIP_PROTOCOL.md](./MESH_GOSSIP_PROTOCOL.md)  
- [PHASE9_DEPLOYMENT_GUIDE.md](./PHASE9_DEPLOYMENT_GUIDE.md) (if present)  
- Skill mirror: [docs/skills/lygo-living-mesh/](./skills/lygo-living-mesh/)  

**Δ9Φ963 — seal locally · mirror freely · gossip roots · the mesh lives.**
