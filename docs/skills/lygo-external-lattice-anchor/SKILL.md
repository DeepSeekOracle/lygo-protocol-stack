---
name: lygo-external-lattice-anchor
description: "Use when the user asks to verify public LYGO lattice mirrors, build a public verify manifest, map eggs to Haven Star Chart proposals, or plan external free-server sync (Pages/HF/Turbo). Layer C world network. Requires LYGO_STACK_ROOT you trust. HTTP GET + local JSON under that stack. Verify is non-mutating by default; snapshot needs --i-consent. No auto git/HF/ClawHub publish."
version: 1.1.0
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
  signature: "Delta9Phi963-EXTERNAL-LATTICE-ANCHOR-v1.1"
  publisher: deepseekoracle
  clawhub: "https://clawhub.ai/deepseekoracle/skills/lygo-external-lattice-anchor"
  github: "https://github.com/DeepSeekOracle/lygo-protocol-stack"
  security_review: "1.1.0-skillspector-harden"
---

# LYGO External Lattice Anchor — Layer C (World Network) v1.1

**Grow the lattice worldwide without abandoning the user.**  
**v1.1 security harden:** no `os.system`, verify non-mutating by default, declared capabilities.

```text
Layer A  Classic kernel eggs     lygo-kernel-egg-planter      data/kernel_eggs/
Layer B  Sovereign seeds         lygo-sovereign-kernel-seeder data/sovereign_seeds/
Layer C  External world network  lygo-external-lattice-anchor public verify + star chart + free servers
Layer D  Living mesh             lygo-living-mesh
Layer E  Agent lattice           lygo-agent-lattice
```

| Surface | URL |
|---------|-----|
| **ClawHub** | https://clawhub.ai/deepseekoracle/skills/lygo-external-lattice-anchor |
| **World lattice doc** | https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/WORLD_LATTICE_LAYER.md |
| **Star Chart LIVE** | https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html |
| **Hub** | https://eternalhaven.ca/ |

**Signature:** `Delta9Phi963-EXTERNAL-LATTICE-ANCHOR-v1.1`  
**License:** LYGO Sovereign License v2.0 (not MIT)

---

## When to use (triggers)

Invoke this skill **only** when the user explicitly wants one of:

1. **Public mirror verify** — HTTP-check LYGO Pages / raw GitHub / Star Chart / anchors  
2. **Build public verify manifest** — local JSON linking A/B roots to public endpoints  
3. **Star Chart egg map proposals** — generate proposals file (not live chart write)  
4. **External sync plan** — dry-run free-server steps; optional local sovereign snapshot with consent  

**Do not** auto-run on generic “check the lattice” without a Layer C / public / external intent.  
**Precondition:** set `LYGO_STACK_ROOT` to a **trusted** lygo-protocol-stack checkout (not untrusted input).

---

## Declared capabilities (least privilege transparency)

| Capability | Default | Notes |
|------------|---------|--------|
| **Network HTTP GET** | Yes (verify scripts) | Public endpoints only; no POST; no credentials |
| **Local file read** | Yes | Stack registries, anchors, manifests |
| **Local file write** | Opt-in / limited | Report JSON under `tests/`; builders write `docs/` when invoked; snapshot needs consent |
| **Shell / os.system** | **No** | Removed in v1.1 |
| **subprocess shell** | **No** | In-process `runpy` allowlist for sibling/stack tools |
| **Git push / HF / ClawHub publish** | **Never** | Human-only outside this skill |
| **Auto-publish** | **No** | |

---

## Mission

1. **Public verify components** — HTTP GET free mirrors.  
2. **Star Chart map** — proposals only (steward ingest separate).  
3. **External plant path** — plan + consent-gated **local** snapshot.  
4. **Sync order** — local A+B first, then C; **local wins**.  
5. **User protection** — external is mirror, not authority.

---

## Install

```bash
clawdhub install lygo-external-lattice-anchor
export LYGO_STACK_ROOT=/path/to/lygo-protocol-stack   # must be trusted
clawdhub install lygo-kernel-egg-planter
clawdhub install lygo-sovereign-kernel-seeder
```

---

## Quick commands

```bash
export LYGO_STACK_ROOT=D:\lygo-protocol-stack

# 1) World verify — READ-mostly (no auto manifest/map refresh)
python scripts/verify_world_lattice.py --json

# Strict read-only (no report file either)
python scripts/verify_world_lattice.py --json --no-write-report

# Opt-in: also rebuild local manifest + star proposals
python scripts/verify_world_lattice.py --json --refresh-local

# 2) Public HTTP verify only (GET). No auto-builder.
python scripts/verify_public_anchors.py --json

# Opt-in: build missing manifest then verify
python scripts/verify_public_anchors.py --json --build-manifest

# 3) Explicit builders (mutating docs/)
python scripts/build_public_verify_manifest.py
python scripts/map_eggs_to_star_chart.py

# 4) Sync PLAN dry-run (no writes beyond stdout)
python scripts/sync_external_plan.py

# 5) Local-only snapshot (consent required)
python scripts/sync_external_plan.py --i-consent --execute-local-only
```

| File | Written by | When |
|------|------------|------|
| `tests/public_anchors_last_run.json` | public verify | default (disable: `--no-write-report`) |
| `tests/world_lattice_last_run.json` | world verify | default (disable: `--no-write-report`) |
| `docs/public_verify_manifest.json` | build_public_verify_manifest | explicit or `--refresh-local` / `--build-manifest` |
| `docs/star_chart_egg_map_proposals.json` | map_eggs_to_star_chart | explicit or `--refresh-local` |
| `docs/sovereign_seeds_snapshot/` | sync_external_plan | `--i-consent --execute-local-only` only |

---

## Synchronization order

```text
1  verify_all_kernel_layers (A+B)     → must not QUARANTINE
2  build_public_verify_manifest       → explicit
3  map_eggs_to_star_chart             → explicit
4  HUMAN consent
5  planter surfaces / snapshot
6  HUMAN git push / HF
7  verify_public_anchors              → GET only
8  star chart steward ingest          → separate skill + consent
```

---

## User protection

1. Local A/B is source of truth.  
2. Consent for snapshot execute / chart live write / publish.  
3. No auto git / HF / ClawHub / social.  
4. QUARANTINE → stop external growth.  
5. Trust only your own `LYGO_STACK_ROOT`.  
6. Verify scripts do **not** shell out via `os.system` (v1.1).  

See `references/SECURITY.md` and `references/AGENT_CONTRACT.md`.

**Δ9Φ963 — local seal · public mirror · star map · human consent · least surprise.**
