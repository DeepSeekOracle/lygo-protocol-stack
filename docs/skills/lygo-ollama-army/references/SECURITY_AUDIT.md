# Security audit notes — lygo-ollama-army v0.7.0

## Process model

| Entry | Spawn model |
|-------|-------------|
| `ollama_army_launcher.py` | In-process threads |
| `ollama_daemon.py` roles | runpy allowlisted stack tools |
| `army_autonomous_supervisor.py` | Threads + runpy; env `LYGO_ARMY_AUTONOMOUS=1` |
| `start_army_full_capacity.ps1` | **OS `python` processes** (operator only) |

## Planting

- `army_self_tune` **cannot** set `planting.enabled=true`  
- Cron plant roles require `planting.enabled` + `planting.consent`  
- Idle plant seeds require `idle_guardian.allow_planting`  
- `run_army_planting.py` re-checks gates  

## External memory

- `three_brain_index` writes army workspace catalog always (local)  
- Appends to `LYRA_CORE/memory` only if `idle_guardian.allow_external_memory_write`  

## Network

- Ollama: `127.0.0.1:11434`  
- Sentinel public page probes: config-gated HTTPS GET  
- Genesis dashboard: bind localhost only  

## Residual risk (accepted)

- Queue tasks execute when a daemon role is running — human must review task JSON  
- Validated `LYGO_STACK_ROOT` tools can mutate stack files if those tools do (operator trust)  
- Operator PS1 is intentionally powerful when dual-gated  

**Δ9Φ963**
