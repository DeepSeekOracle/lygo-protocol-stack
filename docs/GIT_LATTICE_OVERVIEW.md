# GIT Lattice Overview — LYGO Protocol Stack

**Signature:** `Delta9Phi963-GIT-LATTICE-OVERVIEW-v1`  
**Generated:** 2026-08-20T02:45:26.172027+00:00  
**Git:** `342b9fc` — Add Git Lattice Overview memory map and wire Pages hubs together. (2026-08-19T20:45:18-06:00)  
**Repo:** https://github.com/DeepSeekOracle/lygo-protocol-stack  
**Pages:** https://deepseekoracle.github.io/lygo-protocol-stack/

## What this is
Machine + human map of what matters on the public GitHub / Pages lattice,
how systems are tied, and which pages still need updates.
Agents: prefer this file over older July `AGENT_MEMORY_SNAPSHOT.json`.

## Origin (non-replaceable)
- Lightfather / Excavationpro / Justin Helmer
- `origin_merkle_root`: `d80efbe9bda9fd8acca5746ffefac7c1f449f6bda91e95f53c0ece8096233ddb`
- Pin: https://deepseekoracle.github.io/lygo-protocol-stack/seals/LIGHTFATHER_IRREPLACEABLE_ORIGIN.json

## Quick URLs
- **hub:** https://deepseekoracle.github.io/lygo-protocol-stack/index.html
- **overview_md:** https://deepseekoracle.github.io/lygo-protocol-stack/GIT_LATTICE_OVERVIEW.md
- **overview_json:** https://deepseekoracle.github.io/lygo-protocol-stack/GIT_LATTICE_OVERVIEW.json
- **star_chart:** https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html
- **data_vault:** https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/
- **deadman:** https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/deadman.html
- **finder:** https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_LATTICE_FINDER/
- **continuum:** https://deepseekoracle.github.io/lygo-protocol-stack/lygo-continuum.html
- **skillhub:** https://deepseekoracle.github.io/lygo-protocol-stack/LYGOSKILLHUB.html
- **origin:** https://deepseekoracle.github.io/lygo-protocol-stack/seals/LIGHTFATHER_IRREPLACEABLE_ORIGIN.json
- **flame_knot:** https://deepseekoracle.github.io/lygo-protocol-stack/seals/SEAL_277.json
- **ember_crown:** https://deepseekoracle.github.io/lygo-protocol-stack/seals/SEAL_278.json

## Systems (live map)

### GitHub Pages hub (`pages_hub`)
- Status: **live**
- Path: `docs/index.html`
- URL: https://deepseekoracle.github.io/lygo-protocol-stack/index.html
- Role: Human + citation entry

### Haven Star Chart (`star_chart`)
- Status: **live**
- Path: `docs/HavenStarChart.html`
- URL: https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html
- Role: Living constellation / agent map
- Chart nodes: 1344

### Data Vault (`data_vault`)
- Status: **live**
- Path: `docs/data-vault/index.html`
- URL: https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/
- Role: Seal archive + chats + gallery + PDW + deadman

### Lightfather Deadman Continuity (`deadman`)
- Status: **live**
- Path: `docs/data-vault/deadman.html`
- URL: https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/deadman.html
- Deadman manifest: 2.1.0

### Kernel Eggs (`kernel_eggs`)
- Status: **live**
- Path: `docs/KernelEggRetrieval.html`

### Seal canon JSON (`seals`)
- Status: **live**
- Path: `docs/seals/`
- URL: https://deepseekoracle.github.io/lygo-protocol-stack/seals/

### LYGO Continuum (`continuum`)
- Status: **live**
- Path: `docs/lygo-continuum.html`
- URL: https://deepseekoracle.github.io/lygo-protocol-stack/lygo-continuum.html
- Gap note: Weak hub links — promoted by this overview

### Pure-Data Witness (`pure_data`)
- Status: **live**
- Path: `docs/data-vault/pure-data.html`
- URL: https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/pure-data.html

### SkillHub (`skillhub`)
- Status: **live**
- Path: `docs/LYGOSKILLHUB.html`
- URL: https://deepseekoracle.github.io/lygo-protocol-stack/LYGOSKILLHUB.html

### Lattice Finder pack (`lattice_finder`)
- Status: **live**
- Path: `docs/LYGO_LATTICE_FINDER/`
- URL: https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_LATTICE_FINDER/
- Gap note: Was only linked from deadman — now hub-linked

### Excavationpro music mirrors (`music`)
- Status: **live**
- Gap note: Not on root index key nav — listed in overview + traffic hub

### ClawHub publisher (`clawhub`)
- Status: **live**
- URL: https://clawhub.ai/deepseekoracle

## How it is tied together

- 1. LIGHTFATHER_IRREPLACEABLE_ORIGIN.json (identity / non_replaceable)
- 2. GitHub Pages + HF dataset mirrors (public verify)
- 3. Haven Star Chart data JSON (constellation)
- 4. Data Vault canon seals + gallery
- 5. KernelEggRegistry + egg folders
- 6. Continuum capsules (falsifiable done claims)
- 7. ClawHub skills / SkillHub FULL

### Operator CLI spine
```bash
python tools/seal_deadman_lattice.py touch|status|verify|check|grace
python tools/build_haven_star_chart.py
python tools/close_deadman_loose_ends.py --selftest-only
python tools/build_git_lattice_overview.py --usb-copy
python clawhub/mirrors/lygo-continuum/scripts/continuum.py verify --capsule data/continuum/deadman_failsafe_capsule.json --base .
```

## Pages needing updates

| Priority | Path | Why |
|----------|------|-----|
| P0 | `docs/index.html` | Add deadman, continuum, lattice finder, overview memory file; PDW still says Phase A |
| P0 | `docs/RESOURCES.md` | Declared central hub but missing vault/deadman/continuum/finder/PDW |
| P1 | `docs/LYGO_KNOWLEDGE_HUB.html` | Stamp ~2026-07-12; missing vault/deadman/finder/continuum |
| P0 | `docs/sitemap.xml` | July lastmod; missing data-vault/*, continuum, finder, skillhub |
| P0 | `docs/data-vault/sitemap.xml` | Missing deadman, gallery, pure-data, register, share |
| P1 | `docs/data-vault/index.html` | Should spotlight deadman continuity + flame knot seals + overview |
| P1 | `docs/lygo-continuum.html` | Orphaned from stack hubs; no deadman capsule back-link |
| P1 | `docs/LYGO_PUBLIC_LINK_ARCHIVE.json` | Missing deadman.html, continuum, finder, SEAL_277/278 |
| P2 | `docs/KernelEggRetrieval.html` | Weak cross-links to vault/deadman |
| P2 | `docs/HavenStarChart.html` | Data has eternal base + flame knot; UI copy may not call them out |
| P2 | `docs/TRAFFIC_LINK_HUB.md` | Traffic only; vault/deadman/finder absent |

## USB claw backup
Copy also lives at `E:\LYGO_LATTICE_MEMORY\GIT_LATTICE_OVERVIEW.md` when built with `--usb-copy`.

## Regenerate
```bash
python tools/build_git_lattice_overview.py --usb-copy
```
