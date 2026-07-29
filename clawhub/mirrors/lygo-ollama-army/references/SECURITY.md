# SECURITY — lygo-ollama-army v0.8.0

## Declared permissions

| Capability | Default |
|------------|---------|
| Filesystem | Army package workspace (`tasks/`, `results/`, `logs/`, `workspace/`) |
| Optional stack | Only if `LYGO_STACK_ROOT` is a **trusted** clone; **basename** tool allowlist |
| Network default | `127.0.0.1:11434` (Ollama) |
| Network optional | Public HTTPS GET **only if** `sentinel.probe_*=true` **and** role not skipped |
| OS process spawn / shell | **No** |
| In-process runpy | **Yes**, allowlisted scripts only |
| Outbound webhook | **No** |
| Social / Moltx / Moltbook roles | **No** unless `access.social_publish` |
| Planting / registry | **No** unless `planting.enabled` + `consent` |
| Heavy stack roles | **No** unless `access.allow_privileged_roles` |
| git push / HF write / ClawHub publish | **No** |
| Remote LLM | **No** |

## Operator checklist

1. Copy `army_config.example.json` → `army_config.json`  
2. Leave planting, self_tune, idle_guardian, public probes **false** until reviewed  
3. Set `LYGO_STACK_ROOT` only to a clone you control  
4. Never drop unreviewed social/planting tasks into the queue  

## Agents

Do not enable `probe_*`, planting, or external memory writes without explicit human request.
