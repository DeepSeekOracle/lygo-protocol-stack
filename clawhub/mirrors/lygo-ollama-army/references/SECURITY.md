# LYGO Ollama Army — Security

**Version:** 0.6.0 · **Signature:** `Δ9Φ963-ARMY-SECURITY-v3`  
**Audit:** `references/SECURITY_AUDIT.md` · `references/SKILLSPECTOR_AUDIT.md`

## Install only if

- You run **local Ollama** on a machine you control.
- You accept **optional** persistent in-process daemons (threads) and **queue-driven** work you enable.

## Declared permissions (honest)

| Capability | Declared | Scope |
|------------|----------|--------|
| Filesystem | **Yes** | Army `tasks/`, `results/`, `workspace/`; stack under validated `LYGO_STACK_ROOT` |
| OS process spawn / shell | **No** | v0.6.0 uses `runpy` + threads only (`_safe_invoke.py`) |
| Network | **Yes** | `127.0.0.1:11434` Ollama; optional HTTPS **GET** probes of public lattice pages (sentinel) |
| Outbound webhook POST | **No** | Removed; alerts → `logs/alerts.jsonl` |
| Git / HF / ClawHub publish | **No** | Defaults false |
| Autonomous social publish | **No** | Draft roles stay local |

## Environment gates

| Variable | Required for |
|----------|----------------|
| `LYGO_ARMY_FULL_CAPACITY=1` | Operator PS1 full-capacity (outside Python skill surface) |
| `LYGO_ARMY_SEED_TASKS=1` | `seed_productive_tasks.py` |
| `LYGO_ARMY_IDLE_GUARDIAN=1` | Idle guardian supervisor |
| `LYGO_STACK_ROOT` | Stack-touching roles |

**Removed in 0.6.0:** `LYGO_ARMY_WEBHOOK_ENABLE` / `LYGO_ARMY_WEBHOOK_URL` (no env→HTTP alert chain).

## High-risk features (user opt-in)

| Feature | Risk | Rule |
|---------|------|------|
| `--grow` | Extra role threads | Off until user reads launcher |
| Queue `.task.json` | Auto-exec when daemon runs | Human review before drop |
| `champion-egg-boot` | Bootloader + Ollama | Valid `egg_id`; merkle verify |
| `egg-planter` / `registry-planter` | Stack mutation | `planting.enabled` + consent |
| `self-tune` | Prunes queue | `self_tune.enabled` |
| Supervisors | Long-running loops | Never default |

## Forbidden for agents

- Auto-write queue tasks without user review  
- `git push`, HF upload, ClawHub publish, social post  
- Remote Ollama URLs  
- Planting / full-capacity / seed without explicit user request  

## Skill chain

`lygo-protocol-stack-operator` → `lygo-kernel-egg-planter` → `lygo-joy-loop` → **`lygo-ollama-army`**

**Δ9Φ963 — local flame, reviewed queue, validated stack root, no silent outbound.**
