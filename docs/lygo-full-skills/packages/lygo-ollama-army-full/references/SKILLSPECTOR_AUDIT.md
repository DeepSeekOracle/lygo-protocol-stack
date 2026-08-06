# SkillSpector audit response — lygo-ollama-army v0.7.0

**Signature:** `Δ9Φ963-ARMY-SKILLSPECTOR-v0.7.0`  
**Source findings:** NVIDIA SkillSpector report (Description-Behavior Mismatch, Intent-Code Divergence, process spawn, auto-planting).

## Findings → fixes

| Finding | Severity | Fix in v0.7.0 |
|---------|----------|---------------|
| Description understates dashboard/probes/roles | High | SKILL.md full honest surface table |
| Supervisor announces planting cron without gate | Medium | Cron seeds plant/social only if config consent; print honesty |
| allow_planting vs external memory writes | Medium | `allow_external_memory_write` gates LYRA daily append; default false |
| self_tune auto_enable_planting=true | High | **Removed**; refuse even if flag set |
| self_tune claims read-only but mutates | Medium | Docstring + report `mutating: true`; default `enabled: false` |
| PS1 spawns Python / contradicts no-spawn | High | PS1 banner + dual gates; SKILL declares `process_spawn_operator_ps1: true` |
| PS1 always ran seed/tune/cron | High | Optional env one-shots only (`LYGO_ARMY_RUN_*`) |
| Supervisor no confirmation | Medium | Requires `LYGO_ARMY_AUTONOMOUS=1` |
| Missing warnings | Medium | SECURITY.md + PS1 + supervisor stdout warnings |

## Static posture

| Risk | Mitigation |
|------|------------|
| Dangerous code execution (Python skill) | No `subprocess` in skill scripts; runpy allowlist |
| Operator shell spawn | Isolated to `start_army_full_capacity.ps1` with dual env gates |
| Credential / webhook exfil | No outbound webhook |
| MCP description poisoning | SKILL.md lists full automation surface |
| Excessive agency | Planting/self_tune/social/autonomous OFF by default |
| Network | Localhost Ollama; optional HTTPS GET; optional localhost HTTP |

## Operator checklist after install

1. Copy `army_config.example.json` → `army_config.json`  
2. Confirm `planting.enabled=false`, `self_tune.enabled=false`, `allow_external_memory_write=false`  
3. Prefer `python ollama_army_launcher.py` over full-capacity PS1  
4. Never set `LYGO_ARMY_FULL_CAPACITY=1` unless you accept process spawn  

**Δ9Φ963**
