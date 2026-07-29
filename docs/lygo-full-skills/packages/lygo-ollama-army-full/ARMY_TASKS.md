# Army task roles (v0.7.0)

Local Ollama + optional stack tools. **Social pulse roles are not auto-seeded.**

## Safe local roles

| Role | Purpose | Needs stack |
|------|---------|-------------|
| `hb-light` | Light local LLM triage | No |
| `draft-simple` | Local draft text | No |
| `memory-triage` | Local classify/summarize | No |
| `resonance-analyst` | Resonance task notes | No |
| `lattice-check` | `verify_lattice_alignment.py` | Yes |
| `kernel-verify-only` | Kernel egg verify tools | Yes |
| `memory-sync` | Copy public snapshot → army workspace | Yes |
| `clawhub-catalog-audit` | Read local `clawhub/skills.json` | Yes |
| `self-tune` | Local queue hygiene (if enabled) | Optional |

## Explicit opt-in only (not cron default)

| Role | Purpose | Gate |
|------|---------|------|
| `egg-planter` / `registry-planter` | Planting | `planting.enabled` + `consent` |
| `public-pages-check` | Public URL probes | config + allowlisted tool |
| Social / Moltx / Moltbook pulses | **Removed from public cron** | Use separate skills if needed |

## Not included

- Hourly remote LLM / Grok scheduler  
- Outbound webhook  
- Auto git push / HF write  

Drop `.task.json` into `ollama_command_center/tasks/` after human review.
