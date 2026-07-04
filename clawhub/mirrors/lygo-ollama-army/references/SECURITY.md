# LYGO Ollama Army — Security

**Version:** 0.5.0 · **Signature:** `Δ9Φ963-ARMY-SECURITY-v2`  
**Audit:** `references/SECURITY_AUDIT.md` (NVIDIA SkillSpector, 2026-07-04)

## Install only if

- You run **local Ollama** on a machine you control.
- You accept **optional** persistent Python daemons and **queue-driven** execution you enable.

## Declared permissions (ClawHub / MCP transparency)

| Capability | Declared | Scope |
|------------|----------|--------|
| Filesystem | **Yes** | Army `tasks/`, `results/`, `workspace/`; stack tree under validated `LYGO_STACK_ROOT` only |
| Subprocess | **Yes** | `python` argv lists for launcher, daemons, stack tools — **no** `shell=True` |
| Network | **Yes** | `127.0.0.1:11434` (Ollama); HTTPS GET for public page probes (sentinel); outbound webhook **only** if `LYGO_ARMY_WEBHOOK_ENABLE=1` and URL env set |
| Git / HF / ClawHub publish | **No** | `access.github_push`, `access.hf_write`, `access.clawhub_publish` default false |
| Autonomous social publish | **No** | Draft roles are local; human posts elsewhere |

## Required configuration (stack roles)

```bash
export LYGO_STACK_ROOT=/absolute/path/to/lygo-protocol-stack
```

Copy `ollama_command_center/config/army_config.example.json` → `army_config.json` and set `lygo_stack_root`.  
Published ClawHub mirror ships **empty** stack root and **no** preloaded `.task.json` files.

## Environment gates (v0.5.0)

| Variable | Required for |
|----------|----------------|
| `LYGO_ARMY_FULL_CAPACITY=1` | `start_army_full_capacity.ps1` |
| `LYGO_ARMY_SEED_TASKS=1` | `seed_productive_tasks.py` |
| `LYGO_ARMY_WEBHOOK_ENABLE=1` + `LYGO_ARMY_WEBHOOK_URL` | Sentinel outbound webhook |
| `LYGO_OLLAMA_VISIBLE_WINDOWS=1` | Windows titled console daemons |

## High-risk features (user opt-in)

| Feature | Risk | Rule |
|---------|------|------|
| `--grow` | Spawns new daemon roles | Off until user reads launcher |
| Queue `.task.json` | Auto-executes when daemon runs | Human review before drop |
| `champion-egg-boot` | Bootloader + Ollama | Valid `egg_id`; merkle verify |
| `egg-planter` / `registry-planter` | Stack mutation | `planting.enabled` + consent |
| `self-tune` | Prunes queue, may rebuild charts | `self_tune.enabled` in config |
| `army_autonomous_supervisor` | Long-running daemons + cron | Never default; read scripts |

## Forbidden for agents

- Auto-write queue tasks without user review
- `git push`, HF upload, ClawHub publish, Moltbook/Moltx/social post
- Remote Ollama URLs
- `--grow`, full-capacity, seed, webhook, or planting without explicit user request

## Skill chain

`lygo-protocol-stack-operator` → `lygo-kernel-egg-planter` → `lygo-joy-loop` → **`lygo-ollama-army`**

**Δ9Φ963 — local flame, reviewed queue, validated stack root, disclosed permissions.**