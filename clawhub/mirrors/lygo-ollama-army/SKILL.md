---
name: lygo-ollama-army
description: "Local Ollama multi-role army + assistant hub. FULL HONEST SURFACE: (1) Default = in-process threads + STRICT name allowlist runpy (no arbitrary skill .py, no any tools/*.py). (2) Genesis localhost HTTP 127.0.0.1 only; browser open only LYGO_GENESIS_OPEN_BROWSER=1; outbound GitHub/HF/Pages probes only LYGO_GENESIS_PROBE_PUBLIC=1; no Discord/crypto/wallets in status by default. (3) Command-center: sentinel/self_tune/idle/cron/planting all gated OFF; self_tune MUTATES config when enabled and NEVER auto-enables planting. (4) Supervisor needs LYGO_ARMY_AUTONOMOUS=1 + LYGO_ARMY_I_CONSENT=1. (5) PS1 full-capacity OPERATOR-ONLY SPAWNS python.exe. (6) Social pulse / plant roles = optional consent-gated queue labels, not auto engagement. (7) No outbound webhook POST. (8) Desktop installers require LYGO_ARMY_INSTALL_DESKTOP=1. Read references/SECURITY.md first."
version: 0.8.2
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
  version: "0.8.2"
  army_cc: "v0.8.2"
  security_audit: "skillspector-2026-08-06-v0.8.2-full-audit"
  capability_network: "127.0.0.1_ollama_plus_optional_https_get_probes_optional_localhost_http_dashboard"
  publisher: deepseekoracle
  website: "https://deepseekoracle.github.io/Excavationpro/LYGORESONANCE.html"
  signature: "Δ9Φ963-ARMY-SKILL-v0.8.2"
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
    browser_open_default: false
---

# LYGO Ollama Army & Assistant Hub v0.8.2

**SkillSpector-hardened** local Ollama automation. This page is the **full honest surface** — not a minimal marketing blurb.

## Two runtimes (do not confuse)

| Runtime | Process model | Entry |
|---------|---------------|--------|
| **Python skill surface** | In-process threads + `runpy` allowlist | `ollama_army_launcher.py`, supervisor `.py` |
| **Operator PowerShell** | **Spawns** external `python.exe` | `start_army_full_capacity.ps1` only |

Manifest “no subprocess” applies to **Python skill scripts**. The PS1 is explicitly **out of that claim**.

## What this skill actually does

| Surface | Behavior | Default |
|---------|----------|---------|
| **Ollama army** | Multi-role workers as **in-process threads** | Safe entry |
| **Queue** | Reviewed `.task.json` in `ollama_queue/` or `command_center/tasks/` | Manual drop |
| **Champions** | Local persona via `champion_summon.py` (localhost Ollama) | Opt-in |
| **Command center** | Sentinel, self_tune, idle guardian, planting, cron | **OFF** until config/env |
| **self_tune** | **Mutates** `army_config.json` + may prune queue + logs | `self_tune.enabled=false` |
| **Cron** | Seeds **safe** role *names* (lattice/stack/pages/mesh/audit/memory) as queue tasks | Plant/social OFF |
| **Supervisor** | Long loop: sentinel + hourly cron + daemon threads | `LYGO_ARMY_AUTONOMOUS=1` **+** `LYGO_ARMY_I_CONSENT=1` |
| **Stack tools** | Allowlisted **in-process** `runpy` under validated `LYGO_STACK_ROOT` | Opt-in |
| **Genesis dashboard** | Optional **localhost** HTTP `127.0.0.1:9963` | Manual start |
| **Browser open** | Genesis may open system browser | `LYGO_GENESIS_OPEN_BROWSER=1` only |
| **Public probes** | Optional HTTPS **GET** of public lattice pages | Config OFF in example |
| **Alerts** | Local `logs/alerts.jsonl` only | No webhook |
| **Full-capacity PS1** | **Operator shell** — spawns multiple `python.exe` | Triple env gate |

**Not for (defaults):** remote LLM hosts, git push, HF write, ClawHub publish, autonomous social posting, silent planting, silent self_tune, silent browser open.

## Leave disabled unless you need them

| Flag / setting | Risk |
|----------------|------|
| `self_tune.enabled` | Config rewrite + queue prune |
| `self_tune.auto_enable_planting` | **Forced false** — planting never auto-on |
| `planting.enabled` + `planting.consent` | Kernel/registry plant roles |
| `idle_guardian.allow_planting` | Plant-like idle ops blocked unless true |
| `idle_guardian.allow_external_memory_write` | Writes into LYRA_CORE daily index |
| `idle_guardian.allow_stack_mutating_tools` | Chart rebuild / catalog render |
| `social_publish.enabled` / `allow_social_pulse` | Molt* pulse task seeds |
| `access.allow_privileged_roles` | egg-planter / champion-egg-boot threads |
| `sentinel.probe_public_pages` | Outbound HTTPS GET |
| `LYGO_ARMY_AUTONOMOUS=1` + `LYGO_ARMY_I_CONSENT=1` | Long-running supervisor |
| `LYGO_ARMY_FULL_CAPACITY=1` + consent + autonomous | PS1 process-spawn launcher |
| `LYGO_GENESIS_OPEN_BROWSER=1` | System browser open |
| `start_army_full_capacity.ps1` | **Spawns OS Python processes** |

Only set `LYGO_STACK_ROOT` to a **trusted** clone.

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

## Autonomous supervisor (explicit dual consent)

```bash
export LYGO_STACK_ROOT=/absolute/path/to/lygo-protocol-stack
export LYGO_ARMY_AUTONOMOUS=1
export LYGO_ARMY_I_CONSENT=1
python ollama_command_center/scripts/army_autonomous_supervisor.py
```

## Operator full-capacity PS1 (process spawn — not SkillSpector Python path)

```powershell
$env:LYGO_STACK_ROOT = "D:\lygo-protocol-stack"
$env:LYGO_ARMY_FULL_CAPACITY = "1"
$env:LYGO_ARMY_AUTONOMOUS = "1"
$env:LYGO_ARMY_I_CONSENT = "1"
# optional one-shots (each is another python.exe spawn):
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

**Agents:** propose queue JSON only; never enable planting, self_tune, autonomous, full-capacity, seed, social, or browser open without explicit user request.

## Version history

| Ver | Change |
|-----|--------|
| 0.5.0 | Declared permissions, webhook double-gate |
| 0.6.0 | runpy + threads; no outbound webhook |
| 0.7.1 | No auto-plant; self_tune default off; autonomous env gate |
| 0.8.1 | Dual consent supervisor; PS1 triple gate; browser open off |
| **0.8.2** | Full ClawHub audit: strict runpy allowlist; local-only genesis collect; no bak planting config; health probes-only default; no cross-skill cron; no Discord/crypto status; no autostart/push commands; desktop installers gated |

**Δ9Φ963 — local flame, reviewed queue, allowlisted tools, no silent outbound, honest agency.**
