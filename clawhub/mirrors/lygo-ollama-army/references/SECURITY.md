# LYGO Ollama Army — Security

**Version:** 0.7.0 · **Signature:** `Δ9Φ963-ARMY-SECURITY-v4`  
**Audit:** `references/SECURITY_AUDIT.md` · `references/SKILLSPECTOR_AUDIT.md`

## Install only if

- You run **local Ollama** on a machine you control.
- You accept **optional** persistent in-process daemons and **queue-driven** work you enable.
- You understand the **operator PS1** full-capacity path **spawns** `python.exe` (separate from the Python skill surface).

## Declared permissions (honest)

| Capability | Declared | Scope |
|------------|----------|--------|
| Filesystem | **Yes** | Army `tasks/`, `results/`, `workspace/`; stack under validated `LYGO_STACK_ROOT` |
| OS process spawn (Python skill scripts) | **No** | `_safe_invoke.run_python` (runpy) + threads |
| OS process spawn (operator PS1) | **Yes** | `start_army_full_capacity.ps1` only — env gated |
| Network | **Yes** | `127.0.0.1:11434` Ollama; optional HTTPS **GET** public probes; optional localhost HTTP dashboard |
| Outbound webhook POST | **No** | Alerts → `logs/alerts.jsonl` |
| Git / HF / ClawHub publish | **No** | Defaults false |
| Autonomous social publish | **No** | Requires `social_publish` flags |
| Planting | **No** default | `planting.enabled` + `consent`; never auto-enabled by self_tune |

## Environment gates

| Variable | Required for |
|----------|----------------|
| `LYGO_ARMY_AUTONOMOUS=1` | `army_autonomous_supervisor.py` |
| `LYGO_ARMY_FULL_CAPACITY=1` | Operator PS1 full-capacity (process spawn) |
| `LYGO_ARMY_SEED_TASKS=1` | `seed_productive_tasks.py` (PS1 one-shot) |
| `LYGO_ARMY_RUN_SELF_TUNE=1` | PS1 one-shot self_tune spawn |
| `LYGO_ARMY_RUN_CRON=1` | PS1 one-shot cron spawn |
| `LYGO_ARMY_IDLE_GUARDIAN=1` | Idle guardian supervisor |
| `LYGO_STACK_ROOT` | Stack-touching roles (trusted clone only) |

## High-risk features (user opt-in)

| Feature | Risk | Rule |
|---------|------|------|
| `self_tune.enabled` | Config rewrite + queue prune | Default **false**; docstring: **mutating** |
| `auto_enable_planting` | Policy bypass | **Refused** in code even if true |
| Queue `.task.json` | Auto-exec when daemon runs | Human review before drop |
| `egg-planter` / `registry-planter` | Stack mutation | `planting.enabled` + `consent` |
| `allow_external_memory_write` | LYRA_CORE daily write | Default **false** |
| `allow_privileged_roles` | Plant/social/boot roles in supervisor | Default **false** |
| Supervisors | Long-running loops | `LYGO_ARMY_AUTONOMOUS=1` |
| Full-capacity PS1 | Multi-process | Full_CAPACITY + AUTONOMOUS |

## Forbidden for agents

- Auto-write queue tasks without user review  
- `git push`, HF upload, ClawHub publish, social post  
- Remote Ollama URLs  
- Planting / full-capacity / seed / autonomous without explicit user request  
- Enabling `self_tune` or `planting` silently  

## Skill chain

`lygo-protocol-stack-operator` → `lygo-kernel-egg-planter` → `lygo-joy-loop` → **`lygo-ollama-army`**

**Δ9Φ963 — local flame, reviewed queue, validated stack root, no silent outbound, honest spawn boundaries.**
