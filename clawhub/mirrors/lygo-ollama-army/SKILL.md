---
name: lygo-ollama-army
description: "Local Ollama daemons + optional LYGO stack queue roles when LYGO_STACK_ROOT is set. Read references/SECURITY.md and SECURITY_AUDIT.md before install. Not for remote LLM, git push, ClawHub publish, or autonomous social posting."
metadata: {"lygo": true, "ollama": true, "army": true, "champions": true, "consent_required": true, "requires_lygo_stack": false, "version": "0.5.0", "army_cc": "v3", "security_audit": "skillspector-2026-07-04", "capability_network": "127.0.0.1_ollama_plus_optional_user_webhook", "publisher": "deepseekoracle", "website": "https://deepseekoracle.github.io/Excavationpro/LYGORESONANCE.html", "signature": "Δ9Φ963-ARMY-SKILL-v0.5.0", "permissions_declared": {"filesystem": "army_folder_and_validated_LYGO_STACK_ROOT", "subprocess": "local_python_no_shell", "network": "localhost_ollama_and_optional_webhook_if_explicitly_enabled", "git_push": false, "hf_write": false, "clawhub_publish": false, "social_autopublish": false}}
---

# LYGO Ollama Army & Assistant Hub

## Security & install notice (SkillSpector / ClawHub)

This skill is a **real local Ollama automation tool**. It may ship scripts that can **mutate a LYGO stack** if you enable command-center roles, drop tasks into `ollama_command_center/tasks/`, or run full-capacity / cron flows.

**Install only after** reading:

- `references/SECURITY.md`
- `references/SECURITY_AUDIT.md` (NVIDIA SkillSpector response, v0.5.0)
- `references/AGENT_CONTRACT.md`
- `ollama_command_center/config/army_config.example.json`

**Do not** run `start_army_full_capacity.ps1`, `army_autonomous_supervisor.py`, or copy bundled cron examples into `tasks/` unless you **intentionally** want stack audits, self-tuning, egg planting, and registry operations on a clone **you** control.

| Gate | Purpose |
|------|---------|
| `LYGO_STACK_ROOT` | Must point at **your** `lygo-protocol-stack` clone for stack-touching roles |
| `LYGO_ARMY_FULL_CAPACITY=1` | Required for `start_army_full_capacity.ps1` |
| `LYGO_ARMY_SEED_TASKS=1` | Required for `seed_productive_tasks.py` |
| `LYGO_ARMY_WEBHOOK_ENABLE=1` + `LYGO_ARMY_WEBHOOK_URL` | Optional lattice-fail alerts only |

Use a **dedicated folder**. Keep planting / self-tune **disabled** in config until you review source. **No** webhook env vars unless you intend outbound alerts.

**Live companion (LYGO RESONANCE):** https://deepseekoracle.github.io/Excavationpro/LYGORESONANCE.html

---

**Local LLM bot army + optional LYGO champion personas** (127.0.0.1 Ollama only in published tools).

Companion to **lygo-resonance**: queue image batches, resonance-analyst role, champion-assisted **local** creative drafts (human reviews before any public post).

## Core capabilities (summary)

1. **Ollama army** — `ollama_army_launcher.py`, role daemons, queue in `ollama_queue/` or command center `tasks/`.
2. **Champions** — `champion_summon.py` (localhost Ollama only).
3. **Resonance bridge** — `resonance_utility.py` + `resonance-analyst` role.
4. **Optional LYGO command center** — lattice check, joy loop, champion-egg-boot, sentinel (`ollama_command_center/scripts/`). **Opt-in** via config + reviewed tasks.

**Self-grow (`--grow`):** off by default; can spawn extra daemon roles — read launcher source first.

## Safe first run (recommended)

```bash
ollama pull llama3.2:1b
cp ollama_command_center/config/army_config.example.json ollama_command_center/config/army_config.json
# Optional stack roles only:
export LYGO_STACK_ROOT=/absolute/path/to/lygo-protocol-stack
python ollama_army_launcher.py --model llama3.2:1b --roles hb-light,draft-simple,resonance-analyst --count 1
```

Queue example (human writes file after review):

```json
{"id": "task-001", "role": "resonance-analyst", "payload": {"image_path": "photo.jpg", "action": "profile"}}
```

## Agents (TUI / ClawHub)

- **Propose JSON only** for queue tasks; user approves before write.
- **Do not** run full-capacity supervisor, seed scripts, planting, or publish flows without explicit user request.
- **Do not** set webhook or full-capacity env vars for the user.

See `references/AGENT_CONTRACT.md`.

## LYGO stack (optional)

Required only for `lattice-check`, `joy-loop-pulse`, `champion-egg-boot`, planting roles, etc.

```bash
export LYGO_STACK_ROOT=/path/to/lygo-protocol-stack
```

Or set `lygo_stack_root` in `army_config.json` (use example template; **no** machine paths in published mirror defaults).

## Security history (short)

| Version | Hardening |
|---------|-----------|
| 0.3.0 | Localhost-only Ollama; opt-in Windows consoles |
| 0.4.x | Validated stack root; army self-tune fix |
| **0.5.0** | SkillSpector audit: declared permissions, webhook double-gate, no preloaded cron tasks on ClawHub mirror, seed/full-capacity env gates, `SECURITY_AUDIT.md` |

Subprocess use is **intentional** (local Python automation); see `references/SECURITY_AUDIT.md` for finding-by-finding response.

## References

- `references/SECURITY.md` — required
- `references/SECURITY_AUDIT.md` — SkillSpector / ClawHub overview
- `references/AGENT_CONTRACT.md`
- `ollama_command_center/README.md`
- `examples/cron_tasks/` — samples only (not auto-loaded)

**Δ9Φ963 — local flame, reviewed queue, explicit permissions.**