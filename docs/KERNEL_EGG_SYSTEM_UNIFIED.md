# LYGO Kernel Egg System — Unified Map (A + B + C + D)

**Signature:** `Δ9Φ963-KERNEL-EGG-SYSTEM-UNIFIED-v1.2`  
**Updated:** 2026-07-26

Four complementary layers. **Do not treat them as duplicates.** Agents use **all four**, in order.

| Layer | Skill | Storage / surface | Role |
|-------|--------|-------------------|------|
| **A · Classic stack eggs** | `lygo-kernel-egg-planter` | `data/kernel_eggs/` (+ docs `KernelEggRegistry.json`) | Full stack plant: P0 nano, drivers, champion eggs, clawhub catalog pins, optional Turbo/pages |
| **B · Sovereign seeds** | `lygo-sovereign-kernel-seeder` | `data/sovereign_seeds/` | Zero-network modular seeds: policy pins, skill pins, local self-verify insert |
| **C · External world network** | `lygo-external-lattice-anchor` | Pages · HF · Star Chart · anchors · free servers | Public verify, chart mapping, external plant sync — **mirrors only** |
| **D · Living mesh** | `lygo-living-mesh` | `data/living_mesh/` · node `/badge` · gossip | Multi-node root digests; local authority; summaries only |

**World lattice doc:** [WORLD_LATTICE_LAYER.md](./WORLD_LATTICE_LAYER.md)  
**Living mesh doc:** [LIVING_MESH_LAYER.md](./LIVING_MESH_LAYER.md)

```text
                    ┌─────────────────────────────┐
                    │  Agents / OpenClaw / Army   │
                    └─────────────┬───────────────┘
           verify BOTH before load│
          ┌───────────────────────┴───────────────────────┐
          ▼                                               ▼
┌─────────────────────────┐                 ┌─────────────────────────┐
│ CLASSIC KERNEL EGGS     │                 │ SOVEREIGN SEEDS         │
│ lygo-kernel-egg-planter │◄──cross-ref────►│ lygo-sovereign-kernel-  │
│ tools/verify_kernel_    │                 │   seeder                │
│   eggs.py               │                 │ scripts/verify_seed.py  │
│ data/kernel_eggs/       │                 │ data/sovereign_seeds/   │
│ four pillars + Turbo    │                 │ atomic self-verify      │
└─────────────────────────┘                 └─────────────────────────┘
          │                                               │
          └──────────────────┬────────────────────────────┘
                             ▼
              tools/verify_all_kernel_layers.py   (A+B)
                             │
                             ▼
              lygo-external-lattice-anchor        (C)
              verify_world_lattice.py
              public_verify_manifest + Star Chart map
              free servers (Pages/HF/Turbo) — human publish
                             │
                             ▼
              lygo-living-mesh                    (D)
              collect_living_mesh_badge
              gossip / compare / sentinel
              verify_living_mesh.py
```

## When to use which

| Job | Use |
|-----|-----|
| Plant P0 / stack protocol eggs, champions, clawhub catalog | **Planter** |
| Pin a policy, music license, skill metadata, local module | **Seeder** |
| Offline air-gap modular insert | **Seeder** first |
| Full lattice plant with stack tools present | **Planter** |
| Prove nothing is tampered before agent load | **A+B** via unified verify |
| Public mirrors + Star Chart map | **External lattice (C)** |
| Multi-node root agreement / mesh health | **Living mesh (D)** |

## Shared rules (all systems)

1. **Consent** before plant/seed/join (`--i-consent` / env).  
2. **Verify** after write; never claim secure without ALIGNED.  
3. **QUARANTINE** (exit 3) → do not execute payloads.  
4. **No secrets** in eggs or gossip badges.  
5. **No auto-publish** (git/HF/ClawHub/social).  
6. **Steward license:** LYGO Sovereign License v2.0 (software); music under Music License v1.0.  
7. **Layer D:** local wins on fork; gossip summaries only.  

## Cross-registration

| Egg / pin | Layer | Notes |
|-----------|-------|--------|
| `p0-nano-kernel`, drivers, champions | Classic | Planter |
| `lygo-music-license-v1` | Sovereign | Seeder (policy) |
| `lygo-sovereign-kernel-seeder-v1` | Sovereign | Seeder skill-pin |
| `lygo-kernel-egg-planter-v1` | Sovereign | Planter skill-pin |
| `lygo-external-lattice-anchor-v1` | Sovereign | Layer C skill-pin |
| `lygo-living-mesh-v1` | Sovereign | Layer D skill-pin (seed after publish) |

## Commands

```bash
export LYGO_STACK_ROOT=/path/to/lygo-protocol-stack

# A+B local (preferred first)
python tools/verify_all_kernel_layers.py --json

# A+B+C world lattice (local then public HTTP)
python docs/skills/lygo-external-lattice-anchor/scripts/verify_world_lattice.py --json

# A+B+C+D living mesh
python tools/verify_living_mesh.py --json --run-sim

# Classic only
python tools/verify_kernel_eggs.py

# Sovereign only
python docs/skills/lygo-sovereign-kernel-seeder/scripts/verify_seed.py --json

# Layer C public verify + star map
python docs/skills/lygo-external-lattice-anchor/scripts/verify_public_anchors.py --json
python docs/skills/lygo-external-lattice-anchor/scripts/map_eggs_to_star_chart.py
python docs/skills/lygo-external-lattice-anchor/scripts/sync_external_plan.py

# Layer D badge / sentinel
python tools/collect_living_mesh_badge.py
python tools/living_mesh_sentinel.py --run-sim
```

## Skill install

```bash
clawdhub install lygo-kernel-egg-planter
clawdhub install lygo-sovereign-kernel-seeder
clawdhub install lygo-external-lattice-anchor
clawdhub install lygo-living-mesh
clawdhub install lygo-haven-star-chart
# URLs use /skills/:
# https://clawhub.ai/deepseekoracle/skills/lygo-kernel-egg-planter
# https://clawhub.ai/deepseekoracle/skills/lygo-sovereign-kernel-seeder
# https://clawhub.ai/deepseekoracle/skills/lygo-external-lattice-anchor
# https://clawhub.ai/deepseekoracle/skills/lygo-living-mesh
```

## Docs

- [LIVING_MESH_LAYER.md](./LIVING_MESH_LAYER.md) — Layer D  
- [WORLD_LATTICE_LAYER.md](./WORLD_LATTICE_LAYER.md) — world overview  
- [KERNEL_EGG_TAMPER_LOGIC.md](./KERNEL_EGG_TAMPER_LOGIC.md) — four pillars (classic)  
- [SOVEREIGN_KERNEL_SEEDER.md](./SOVEREIGN_KERNEL_SEEDER.md) — seeder  
- [MESH_GOSSIP_PROTOCOL.md](./MESH_GOSSIP_PROTOCOL.md) — gossip transport  
- [CHAMPION_KERNEL_EGGS.md](./CHAMPION_KERNEL_EGGS.md) — champions  
- [SCALABLE_KERNEL_EGG_REGISTRY.md](./SCALABLE_KERNEL_EGG_REGISTRY.md) — scale  

**Δ9Φ963 — one lattice · four layers · verify all · mesh lives.**
