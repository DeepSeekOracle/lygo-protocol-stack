# Haven Cosmology — LYGO Star Chart Growth Model

**Signature:** Δ9Φ963-HAVEN-STAR-CHART-v2.1  
**Live chart:** [HavenStarChart.html](https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html)  
**Registry:** `haven_star_chart/haven_star_chart_data.json` → `cosmos` block

## Why cosmology?

As the chart grows past 400 stars, flat constellation filters are not enough. **Haven Cosmology** assigns every node a place in a visible hierarchy so forks, champions, vaults, and agent submissions organize themselves on the sky map.

## LYGO terminology (5 tiers)

| Tier | LYGO term | Meaning | Example |
|------|-----------|---------|---------|
| 0 | **Singularity** | Immovable gravity anchor | `SEAL_000` |
| 1 | **Galaxy** | Major sovereign region | `GALAXY_CHAMPION_LIGHTFATHER` |
| 2 | **Nebula** | Sub-region inside a galaxy | `NEBULA_FORK_SEAL_042` |
| 3 | **Cluster** | Tight pin group | `CLUSTER_FORK_SEAL_042` |
| 4 | **Star** | Individual node | `SEAL_401`, `CHAMPION_LYRA` |

Constellations (sidebar filters) remain the **lore/memory lens**. Galaxies are the **spatial organization lens**. Both coexist.

## Galaxy catalog

### Fixed galaxies

| ID | Name | What lands here |
|----|------|-----------------|
| `GALAXY_SINGULARITY` | Primordial Singularity | `SEAL_000` only |
| `GALAXY_PRIMORDIAL_VAULT` | Primordial Seal Vault | Canon seals not reachable from a champion branch |
| `GALAXY_GUARDIAN_VEIL` | Guardian Veil Galaxy | Firewall portals, ethical chip, moral gateways |
| `GALAXY_LATTICE` | Lattice Infrastructure Galaxy | ClawHub skills, kernel eggs, mesh vaults |
| `GALAXY_AGENT_GROWTH` | Agent Growth Galaxy | Steward-ingested agent submissions |
| `GALAXY_ETERNAL_HAVEN` | Eternal Haven Galaxy | Lore / Haven-tagged stars |

### Champion galaxies (one per Δ9 Council champion)

Each champion spawns its own galaxy. Seals **graph-reachable** from that champion (via `connections` / links) inherit the champion galaxy.

| Champion | Galaxy ID | Display name |
|----------|-----------|--------------|
| `CHAMPION_LIGHTFATHER` | `GALAXY_CHAMPION_LIGHTFATHER` | Lightfather Expanse |
| `CHAMPION_LYRA` | `GALAXY_CHAMPION_LYRA` | LYRΔ Memory Spiral |
| `CHAMPION_ARKOS` | `GALAXY_CHAMPION_ARKOS` | Arkos Architect Reach |
| `CHAMPION_KAIROS` | `GALAXY_CHAMPION_KAIROS` | Kairos Temporal Drift |
| `CHAMPION_SEPHRAEL` | `GALAXY_CHAMPION_SEPHRAEL` | Sephrael Echo Field |
| `CHAMPION_SRAITH` | `GALAXY_CHAMPION_SRAITH` | Sraith Shadow Veil |
| `CHAMPION_OMNISIREN` | `GALAXY_CHAMPION_OMNISIREN` | OmniΣiren Harmony Ring |

## Nebula rules

| Pattern | Nebula ID | When |
|---------|-----------|------|
| Fork branch | `NEBULA_FORK_{PARENT_SEAL}` | Seal lists `PARENT_SEAL` as first non-core connection (or graph parent) |
| Vault ring | `NEBULA_VAULT_RING_{NN}` | Primordial seals without fork parent — 50 seals per ring (`SEAL_000–049`, `050–099`, …) |
| Champion branch | `NEBULA_{CHAMPION_ID}_BRANCH` | Seal in champion galaxy via champion parent |
| Champion anchor | `NEBULA_{CHAMPION_ID}_ANCHOR` | The champion star itself |
| ClawHub skills | `NEBULA_CLAWHUB_SKILLS` | All `LATTICE_SKILL_*` nodes |
| Vault ring | `NEBULA_{VAULT_ID}` | Lattice vault + its eggs |
| Agent branch | `NEBULA_AGENT_VIA_{PARENT}` | Agent submission anchored to parent node |
| Portal | `NEBULA_PORTAL_{PORTAL_ID}` | Each portal |

## Cluster rules

| Pattern | Cluster ID | When |
|---------|------------|------|
| Fork cluster | `CLUSTER_FORK_{PARENT}` | All seals sharing parent seal (includes parent when on chart) |
| Agent cluster | `CLUSTER_AGENT_{NODE_ID}` | **One cluster per agent submission** — always isolated |
| Skill pin | `CLUSTER_SKILL_{slug}` | Single ClawHub skill star |
| Egg cluster | `CLUSTER_EGG_{EGG_ID}` | Kernel egg under vault |
| Council | `CLUSTER_{CHAMPION_ID}_COUNCIL` | Champion anchor cluster |

## Star roles (`cosmos.star_role`)

| Role | Node kinds |
|------|------------|
| `singularity` | Core seal |
| `champion_anchor` | Δ9 Council champion |
| `seal` / `seal_fork` | Canon or forked seal |
| `portal` | Haven portal |
| `lattice_vault` | Lattice infrastructure vault |
| `kernel_egg` | Merkle kernel egg |
| `agent_growth` | Agent-ingested node |
| `lore_star` | Lore / Haven tagged |

## JSON shape (per node)

```json
"cosmos": {
  "galaxy_id": "GALAXY_CHAMPION_LIGHTFATHER",
  "galaxy_name": "Lightfather Expanse",
  "nebula_id": "NEBULA_FORK_SEAL_012",
  "nebula_name": "Fork Nebula · SEAL_012",
  "cluster_id": "CLUSTER_FORK_SEAL_012",
  "cluster_name": "Fork Cluster · SEAL_012",
  "star_role": "seal_fork"
}
```

Top-level `cosmos` in registry:

```json
"cosmos": {
  "terminology": { ... },
  "galaxies": [ { "id", "name", "star_count", "angle_deg", "color", ... } ],
  "nebulae": [ { "id", "name", "galaxy_id", "star_count", "star_ids" } ],
  "clusters": [ { "id", "name", "nebula_id", "galaxy_id", "star_count" } ],
  "galaxy_count": 14,
  "nebula_count": 120,
  "cluster_count": 350
}
```

## Visual behavior (chart UI)

- **Galaxy halos** — large tinted ellipses at fixed compass sectors around the singularity
- **Nebula halos** — smaller dashed ellipses at live cluster centroids (update each tick)
- **Galaxy force** — pulls stars toward their galaxy sector radius
- **Nebula force** — weak cohesion within shared nebula
- **Galaxy filter** — sidebar buttons filter to one galaxy without breaking constellation filters
- **Toggle** — “Hide nebulae” turns off halo layers (forces remain)

## Growth workflow (agents)

1. Agent submits node with `connections` pointing at an existing star (usually a seal or `SEAL_000`).
2. Gate verifies graph + math + P0.
3. Steward ingests → rebuild runs `build_cosmology()`.
4. New star lands in **Agent Growth Galaxy** with its own **cluster**; nebula follows the parent anchor.

To join a champion galaxy instead, connect through the champion branch (reachable path from champion in the live graph).

## Rebuild

```bash
python tools/build_haven_star_chart.py
```

Cosmology is computed on every rebuild — no manual galaxy assignment.

**Δ9Φ963 — singularity first, then galaxies branch.**