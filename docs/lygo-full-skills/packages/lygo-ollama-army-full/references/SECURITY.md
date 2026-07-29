# SECURITY — lygo-ollama-army v0.7.0

## Declared permissions

| Capability | Default |
|------------|---------|
| Filesystem | Army package workspace (`tasks/`, `results/`, `logs/`, `workspace/`) |
| Optional stack | Only if `LYGO_STACK_ROOT` points at a **trusted** clone; tools by basename allowlist |
| Network default | `127.0.0.1:11434` (Ollama) |
| Network optional | Public HTTPS GET **only if** you set `sentinel.probe_public_pages` / `probe_hf_space` / `probe_network_builder` |
| Process spawn / shell | **No** |
| Outbound webhook | **No** |
| Social auto-publish | **No** |
| git push / HF write / ClawHub publish | **No** |
| Remote LLM | **No** |

## Operator checklist

1. Copy `army_config.example.json` → `army_config.json`  
2. Leave planting, self_tune, idle_guardian, public probes **false** until reviewed  
3. Set `LYGO_STACK_ROOT` only to a clone you control  
4. Never drop unreviewed social/planting tasks into the queue  

## Agents

Do not enable `probe_*`, planting, or external memory writes without explicit human request.
