---
name: lygo-external-lattice-anchor
description: "LYGO External Lattice Anchor (Layer C / world network) — public verify components, Haven Star Chart egg mapping, external plant to free internet surfaces (Pages/HF/Turbo). Synchronizes with classic eggs (A) and sovereign seeds (B). Protects users: consent-gated, local authority, no auto-publish."
version: 1.0.0
license: LYGO-Sovereign-v2.0
metadata:
  openclaw:
    emoji: "🌐"
    homepage: "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/WORLD_LATTICE_LAYER.md"
    requires:
      anyBins: [python, python3]
  lygo: true
  lattice: true
  external: true
  world_network: true
  layer: "C"
  signature: "Delta9Φ963-EXTERNAL-LATTICE-ANCHOR-v1.0"
  publisher: deepseekoracle
  clawhub: "https://clawhub.ai/deepseekoracle/skills/lygo-external-lattice-anchor"
  github: "https://github.com/DeepSeekOracle/lygo-protocol-stack"
---

# LYGO External Lattice Anchor — Layer C (World Network)

**Grow the lattice worldwide without abandoning the user.**

```text
Layer A  Classic kernel eggs     lygo-kernel-egg-planter      data/kernel_eggs/
Layer B  Sovereign seeds         lygo-sovereign-kernel-seeder data/sovereign_seeds/
Layer C  External world network  lygo-external-lattice-anchor public verify + star chart + free servers
```

| Surface | URL |
|---------|-----|
| **ClawHub** | https://clawhub.ai/deepseekoracle/skills/lygo-external-lattice-anchor |
| **World lattice doc** | https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/WORLD_LATTICE_LAYER.md |
| **Star Chart LIVE** | https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html |
| **Star Chart portal** | https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChartPortal.html |
| **Egg retrieval UI** | https://deepseekoracle.github.io/lygo-protocol-stack/KernelEggRetrieval.html |
| **Hub** | https://eternalhaven.ca/ |

**Signature:** `Delta9Φ963-EXTERNAL-LATTICE-ANCHOR-v1.0`  
**License:** LYGO Sovereign License v2.0 (not MIT)

---

## Mission

1. **Public verify components** — HTTP-check free mirrors (Pages, raw GitHub, HF, Star Chart, anchors).  
2. **Star Chart map** — turn A/B eggs + surfaces into **proposals** for Haven Star Chart (steward ingest).  
3. **External plant path** — plan (and consent-gated local snapshot) that feeds planter surfaces: Pages registry, Turbo, HF, ClawHub metadata.  
4. **Synchronization** — one world-verify pipeline: local A+B first, then C; **local wins** on conflict.  
5. **User protection** — external is **mirror, not authority**; no auto push/upload; quarantine on local hash fail.

---

## Install

```bash
clawdhub install lygo-external-lattice-anchor
export LYGO_STACK_ROOT=/path/to/lygo-protocol-stack
# also install layers A + B
clawdhub install lygo-kernel-egg-planter
clawdhub install lygo-sovereign-kernel-seeder
clawdhub install lygo-haven-star-chart
```

---

## Quick commands

```bash
export LYGO_STACK_ROOT=D:\lygo-protocol-stack   # example

# 1) World verify (A+B local, then C public)
python scripts/verify_world_lattice.py --json

# 2) Public verify components only (network)
python scripts/verify_public_anchors.py --json

# 3) Build public verify manifest (links all layers + endpoints)
python scripts/build_public_verify_manifest.py

# 4) Map eggs → Star Chart proposals (does NOT live-write chart)
python scripts/map_eggs_to_star_chart.py

# 5) External sync PLAN (dry-run)
python scripts/sync_external_plan.py

# 6) Local-only snapshot sovereign → docs/ (consent)
python scripts/sync_external_plan.py --i-consent --execute-local-only
```

Outputs (under stack):

| File | Purpose |
|------|---------|
| `docs/public_verify_manifest.json` | Layer A/B/C + public endpoints |
| `docs/star_chart_egg_map_proposals.json` | Star Chart proposals for steward |
| `tests/public_anchors_last_run.json` | Last HTTP verify |
| `tests/world_lattice_last_run.json` | Full world verdict |

---

## Synchronization order (agents must follow)

```text
1  verify_all_kernel_layers (A+B)     → must not QUARANTINE
2  build_public_verify_manifest
3  map_eggs_to_star_chart
4  HUMAN consent
5  planter --surfaces local,registry,pages,turbo   (layer A externalize)
6  sovereign snapshot → docs/                      (layer B mirror)
7  HUMAN git push  → GitHub Pages / raw
8  HUMAN HF push   → free dataset servers
9  verify_public_anchors
10 star chart steward ingest (lygo-haven-star-chart --i-consent)
```

**Never skip 1 for 7–10.** Public network grows from verified local truth.

---

## Free internet / worldwide anchors

| Surface | Role |
|---------|------|
| GitHub Pages | Public HTTP verify UI + registries |
| GitHub raw | IMMUTABLE_ANCHORS + sovereign snapshot |
| Hugging Face | Free dataset mirrors (stack + music CAS) |
| Arweave Turbo | Optional small permaweb anchors (planter) |
| ClawHub | Skill metadata worldwide |
| Haven Star Chart | Living map of eggs + surfaces |
| Eternalhaven / asiancoastline | Human-facing portals |

---

## User protection (non-negotiable)

1. **Local A/B is source of truth** — if public JSON disagrees, re-publish after local verify; do not “fix local from public” blindly.  
2. **Consent** for any plant, snapshot execute, chart ingest, push.  
3. **No auto git / HF / ClawHub / social.**  
4. **QUARANTINE** on local tamper — stop; do not push bad eggs.  
5. **P0** before destructive path ops.  
6. **No secrets** in public manifests or eggs.  
7. Public HTTP failures → **PUBLIC_WARN** (soft) unless `--strict-public`.

---

## Skill chain

```text
lygo-protocol-stack-operator
  → lygo-network-builder          (anchor verify)
  → lygo-kernel-egg-planter       (A)
  → lygo-sovereign-kernel-seeder  (B)
  → lygo-external-lattice-anchor  (C)  ← this skill
  → lygo-haven-star-chart         (map ingest)
  → lygo-mesh-deploy              (optional gossip)
```

---

## Agent contract

See `references/AGENT_CONTRACT.md` and `references/SECURITY.md`.

**Δ9Φ963 — local seal · public mirror · star map · human consent · world lattice grows in light.**
