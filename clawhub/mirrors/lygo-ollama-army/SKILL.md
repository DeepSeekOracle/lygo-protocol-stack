---
name: lygo-ollama-army
description: "Local Ollama multi-role army. Default path: in-process threads + allowlisted runpy (no subprocess). Optional localhost HTTP dashboard/genesis. Optional HTTPS GET public lattice probes. Supervisors/self_tune/planting/social/full-capacity PS1 are env/config gated and OFF by default. Operator PowerShell full-capacity intentionally spawns python.exe — not the no-spawn path. No outbound webhook, no auto git/HF/ClawHub/social. Read references/SECURITY.md first."
version: 0.7.1
license: LYGO-Sovereign-v2.0
metadata:
  openclaw:
    emoji: "🪖"
    homepage: "https://github.com/DeepSeekOracle/lygo-protocol-stack"
    requires:
      anyBins: [python, python3]
  lygo: true
  ollama: true
  army: true
  champions: true
  consent_required: true
  requires_lygo_stack: false
  version: "0.7.1"
  army_cc: "v0.7.1"
  security_audit: "skillspector-2026-08-06-v0.7.1"
  capability_network: "127.0.0.1_ollama_plus_optional_https_get_probes"
  publisher: deepseekoracle
  website: "https://deepseekoracle.github.io/Excavationpro/LYGORESONANCE.html"
  signature: "Δ9Φ963-ARMY-SKILL-v0.7.1"
  permissions_declared:
    filesystem: "army_folder_and_validated_LYGO_STACK_ROOT"
    process_spawn_python_skill: false
    process_spawn_operator_ps1: true
    shell_operator_ps1: true
    network: "localhost_ollama_optional_public_https_get_probes_optional_localhost_http_dashboard"
    outbound_webhook: false
    git_push: false
    hf_write: false
    clawhub_publish: false
    social_autopublish: false
    planting_default: false
    self_tune_default: false
---

# LYGO Ollama Army & Assistant Hub v0.7.1

**SkillSpector-hardened** local Ollama automation for LYGO operators.

## What this skill actually does (full honest surface)

| Surface | Behavior | Default |
|---------|----------|---------|
| **Ollama army** | Multi-role workers as **in-process threads** (`ollama_army_launcher.py`) | Safe entry |
| **Queue** | Reviewed `.task.json` in `ollama_queue/` or `ollama_command_center/tasks/` | Manual drop |
| **Champions** | Local persona via `champion_summon.py` (localhost Ollama) | Opt-in |
| **Command center** | Sentinel, self-tune, idle guardian, planting, cron | **OFF** until config/env |
| **self_tune** | **Mutates** `army_config.json` + may prune queue | `self_tune.enabled=false` |
| **Cron** | Seeds **safe** roles only; plant/social gated | Plant/social OFF |
| **Supervisor** | Long loop: sentinel + hourly cron + daemon threads | `LYGO_ARMY_AUTONOMOUS=1` |
| **Stack tools** | Allowlisted **in-process** `runpy` under validated `LYGO_STACK_ROOT` | Opt-in |
| **Genesis / dashboard** | Optional **localhost** HTTP (`127.0.0.1`) | Manual start |
| **Public probes** | Optional HTTPS **GET** of public lattice pages (sentinel) | Config OFF in example |
| **Alerts** | Local `logs/alerts.jsonl` only | No webhook |
| **Full-capacity PS1** | **Operator shell** — spawns multiple `python.exe` | `LYGO_ARMY_FULL_CAPACITY=1` + `LYGO_ARMY_AUTONOMOUS=1` |

**Not for (defaults):** remote LLM hosts, git push, HF write, ClawHub publish, autonomous social posting, silent planting, silent self-tune.

---

## Leave disabled unless you need them

| Flag / setting | Risk |
|----------------|------|
| `self_tune.enabled` | Config rewrite + queue prune |
| `self_tune.auto_enable_planting` | **Ignored / refused** in v0.7 — planting never auto-on |
| `planting.enabled` + `planting.consent` | Kernel/registry plant roles |
| `idle_guardian.allow_planting` | Idle plant seeds |
| `idle_guardian.allow_external_memory_write` | Writes into LYRA_CORE daily index |
| `social_publish.enabled` / `allow_social_pulse` | Molt* pulse task seeds |
| `access.allow_privileged_roles` | egg-planter / champion-egg-boot threads |
| `sentinel.probe_public_pages` | Outbound HTTPS GET |
| `LYGO_ARMY_AUTONOMOUS=1` | Long-running supervisor |
| `LYGO_ARMY_FULL_CAPACITY=1` | PS1 process-spawn launcher |
| `LYGO_ARMY_SEED_TASKS=1` | Productive seed script |
| `start_army_full_capacity.ps1` | **Spawns OS Python processes** |

Only set `LYGO_STACK_ROOT` to a **trusted** clone.

---

## Install

```bash
npx clawhub@latest install deepseekoracle/lygo-ollama-army
ollama pull llama3.2:1b
cp ollama_command_center/config/army_config.example.json ollama_command_center/config/army_config.json
```

## Safe first run (recommended)

```bash
python ollama_army_launcher.py --model llama3.2:1b --roles hb-light,draft-simple,resonance-analyst --count 1
```

## Autonomous supervisor (explicit)

```bash
export LYGO_STACK_ROOT=/absolute/path/to/lygo-protocol-stack
export LYGO_ARMY_AUTONOMOUS=1
python ollama_command_center/scripts/army_autonomous_supervisor.py
```

## Operator full-capacity PS1 (process spawn — not SkillSpector Python path)

```powershell
$env:LYGO_STACK_ROOT = "D:\lygo-protocol-stack"
$env:LYGO_ARMY_FULL_CAPACITY = "1"
$env:LYGO_ARMY_AUTONOMOUS = "1"
# optional one-shots:
# $env:LYGO_ARMY_RUN_SELF_TUNE = "1"   # only if self_tune.enabled in config
# $env:LYGO_ARMY_SEED_TASKS = "1"
# $env:LYGO_ARMY_RUN_CRON = "1"
.\start_army_full_capacity.ps1
```

## Security

Read **before** install:

- `references/SECURITY.md`
- `references/SECURITY_AUDIT.md`
- `references/SKILLSPECTOR_AUDIT.md`
- `references/AGENT_CONTRACT.md`

**Agents:** propose queue JSON only; never enable planting, self_tune, autonomous, full-capacity, seed, or social without explicit user request.

## Version history

| Ver | Change |
|-----|--------|
| 0.5.0 | Declared permissions, webhook double-gate |
| 0.6.0 | runpy + threads; no outbound webhook |
| **0.7.1** | SkillSpector findings: no auto-plant; self_tune default off + honest mutating docs; cron plant/social gated; external memory write gated; autonomous env gate; PS1 honest spawn warnings |

**Δ9Φ963 — local flame, reviewed queue, allowlisted tools, no silent outbound, honest agency.**
