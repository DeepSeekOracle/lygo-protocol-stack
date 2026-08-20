# GIT Lattice Overview v2 — full repo census

**Signature:** `Delta9Phi963-GIT-LATTICE-OVERVIEW-v2`  
**Generated:** 2026-08-20T02:48:45.384773+00:00  
**Git:** `82d0d4b` — Refresh Git Lattice Overview to HEAD 342b9fc + USB claw copy  
**Full scan:** YES — `4085` tracked files

## Scope honesty
v1 mapped Pages hubs (~12 systems). **v2 adds a full `git ls-files` census** of the repository:
protocols, tools, data/, clawhub mirrors, products, tests, CI, docs HTML orphans.

- Full census: [docs/GIT_REPO_CENSUS.md](docs/GIT_REPO_CENSUS.md) · [docs/GIT_REPO_CENSUS.json](docs/GIT_REPO_CENSUS.json)

## Repo scale

| Metric | Count |
|--------|------:|
| Tracked files | 4085 |
| docs HTML pages | 57 |
| tools/*.py | 299 |
| ClawHub mirrors | 82 |
| Protocol dirs | 11 |
| Orphan HTML (href-scan) | 11 |

### Buckets

- `docs_pages`: 2468
- `clawhub`: 721
- `tools`: 329
- `data_runtime`: 275
- `products`: 102
- `protocols`: 66
- `tests`: 66
- `other`: 24
- `hf_deploy`: 12
- `stack_core`: 12
- `repo_root`: 6
- `ci`: 4

### Protocols

`protocol0_byte_entropy_filter`, `protocol1_memory_mycelium`, `protocol2_cognitive_bridge`, `protocol3_vortex_consensus`, `protocol4_ascension_engine`, `protocol5_harmony_node`, `protocol6_quantum_attest`, `protocol7_human_ai_interface`, `protocol8_ldq_synthesis`, `protocol9_failsafe`, `protocol_bridge`

### Products

`lygo_highperf`, `lygo_lpis`, `lygo_openclaw`, `lygo_sandcastle`, `lygo_second_brain`, `lygo_smart_disk`, `pxpipe_lygo`

## Must-haves

All checklist paths present.

## Medium-severity orphan HTML (sample)

- `docs/EternalHavenCodex.html`
- `docs/data-vault/share.html`
- `docs/joy_loop/dashboard/architect.html`
- `docs/lygo-claw-usb/dashboard/lygo-claw.html`

## Public systems (from v1 map)

- **GitHub Pages hub** (`pages_hub`) — https://deepseekoracle.github.io/lygo-protocol-stack/index.html
- **Haven Star Chart** (`star_chart`) — https://deepseekoracle.github.io/lygo-protocol-stack/HavenStarChart.html
- **Data Vault** (`data_vault`) — https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/
- **Lightfather Deadman Continuity** (`deadman`) — https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/deadman.html
- **Kernel Eggs** (`kernel_eggs`) — docs/KernelEggRetrieval.html
- **Seal canon JSON** (`seals`) — https://deepseekoracle.github.io/lygo-protocol-stack/seals/
- **LYGO Continuum** (`continuum`) — https://deepseekoracle.github.io/lygo-protocol-stack/lygo-continuum.html
- **Pure-Data Witness** (`pure_data`) — https://deepseekoracle.github.io/lygo-protocol-stack/data-vault/pure-data.html
- **SkillHub** (`skillhub`) — https://deepseekoracle.github.io/lygo-protocol-stack/LYGOSKILLHUB.html
- **Lattice Finder pack** (`lattice_finder`) — https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_LATTICE_FINDER/
- **Excavationpro music mirrors** (`music`) — None
- **ClawHub publisher** (`clawhub`) — https://clawhub.ai/deepseekoracle

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
- **census_md:** https://deepseekoracle.github.io/lygo-protocol-stack/GIT_REPO_CENSUS.md
- **census_json:** https://deepseekoracle.github.io/lygo-protocol-stack/GIT_REPO_CENSUS.json

## USB claw
`E:\LYGO_LATTICE_MEMORY\` — overview + census copies when built with `--usb-copy`.

## Regenerate
```bash
python tools/build_git_lattice_overview.py --usb-copy
python tools/census_git_lattice.py --usb-copy
```
