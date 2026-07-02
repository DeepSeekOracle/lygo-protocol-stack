# Productive army tasks (set-and-review-later)

## One-shot seed (lattice / stack / ClawHub)

```bash
cd path/to/lygo-ollama-army
set LYGO_STACK_ROOT=I:\E Drive\lygo-protocol-stack
python seed_productive_tasks.py
```

Daemons (already running or launch with launcher) drain `ollama_queue/*.task.json` → `ollama_results/*.result.json`.

## Task types

| Role | What it does | Needs Ollama |
|------|----------------|--------------|
| `lattice-check` | Runs `verify_lattice_alignment.py` | No |
| `stack-integrity` | Runs `run_sovereign_integrity_test.py` | No |
| `clawhub-catalog-audit` | Reads `clawhub/skills.json` stats | No |
| `public-pages-check` | Runs `verify_public_pages.py` | No |
| `audit-suite` | SLM + phase7 + phase9 audits | No |
| `memory-sync` | Copies snapshot → `workspace/LYGO_MEMORY_SYNC.json` | No |
| `egg-planter` | Lattice OK → preflight/smoke → **kernel egg plant** (consent in `army_config.planting`) | No |
| `registry-planter` | Lattice OK → CAS **registry plant** + verify (`cas_registry_cli`) | No |
| `mesh-cartographer` | Runs `lygo_network_builder_verify.py` (SLM anchors) | No |
| `memory-triage` / `hb-light` | Champion-style JSON review prompts | Yes |
| `draft-simple` | Upgrade copy / public blurbs | Yes |

## Full capacity (Windows)

```powershell
.\start_army_full_capacity.ps1
```

Uses `ollama_command_center/config/army_config.json` **v3** — all roles + `mesh-cartographer` + 2× `hb-light` + ARKOS on triage/draft.

## Re-seed anytime

Safe to run `seed_productive_tasks.py` again after lattice or ClawHub changes.

## Command Center (hands)

`ollama_command_center/` — sentinel, dashboard, cron, config (`access.*_write: false`).

```bash
python ollama_command_center/scripts/sentinel_heartbeat.py --loop
python ollama_command_center/scripts/army_cron_once.py
```

Hourly Grok scheduler task seeded for `army_cron_once.py`.

## Planting (v3)

`army_config.json` → `planting.enabled`, `planting.consent`, `egg_surfaces`, `local_only_anchor`.  
No GitHub/HF/ClawHub push (`access.*_write: false`).  
Artifacts: `workspace/egg_plant_last_run.json`, `registry_plant_last_run.json`.

```bash
python ollama_command_center/scripts/run_army_planting.py all
```

```bash
python ollama_command_center/scripts/verify_army_tuning.py
```

**Δ9Φ963-ARMY-TASKS-v4**