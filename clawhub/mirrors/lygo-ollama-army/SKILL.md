---
name: lygo-ollama-army
description: "Local Ollama multi-role army (in-process threads) + queue tasks + optional stack tools under validated LYGO_STACK_ROOT via allowlisted runpy. Local dashboard/genesis, sentinel with local alerts only. No OS process spawn, no outbound webhook, no remote LLM, no auto git/HF/ClawHub/social publish. Read references/SECURITY.md first."
version: 0.6.0
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
  version: "0.6.0"
  army_cc: "v3"
  security_audit: "skillspector-2026-07-29-v0.6.0"
  capability_network: "127.0.0.1_ollama_plus_optional_https_get_probes"
  publisher: deepseekoracle
  website: "https://deepseekoracle.github.io/Excavationpro/LYGORESONANCE.html"
  signature: "Δ9Φ963-ARMY-SKILL-v0.6.0"
  permissions_declared:
    filesystem: "army_folder_and_validated_LYGO_STACK_ROOT"
    process_spawn: false
    shell: false
    network: "localhost_ollama_and_optional_public_https_get_probes"
    outbound_webhook: false
    git_push: false
    hf_write: false
    clawhub_publish: false
    social_autopublish: false
---

# LYGO Ollama Army & Assistant Hub v0.6.0

**SkillSpector-hardened** local Ollama automation for LYGO operators.

## What this skill actually does (honest surface)

| Surface | Behavior |
|---------|----------|
| **Ollama army** | Multi-role workers as **in-process threads** (`ollama_army_launcher.py` → `ollama_daemon.run_daemon`) |
| **Queue** | Drop reviewed `.task.json` into `ollama_queue/` or `ollama_command_center/tasks/` |
| **Champions** | Local persona injection via `champion_summon.py` / `--champion` (localhost Ollama only) |
| **Command center** | Sentinel, self-tune, idle guardian, planting gates — **opt-in** via config + consent |
| **Stack tools** | Optional: allowlisted **in-process** `runpy` of stack `tools/*.py` when `LYGO_STACK_ROOT` validates |
| **Genesis console** | Optional **localhost** HTTP dashboard (`127.0.0.1` only) |
| **Alerts** | **Local** `logs/alerts.jsonl` only — **no** outbound webhook HTTP |

**Not for:** remote LLM hosts, git push, HF write, ClawHub publish, autonomous social posting, shell process spawn.

---

## Install

```bash
npx clawhub@latest install deepseekoracle/lygo-ollama-army
ollama pull llama3.2:1b
cp ollama_command_center/config/army_config.example.json ollama_command_center/config/army_config.json
```

## Safe first run

```bash
python ollama_army_launcher.py --model llama3.2:1b --roles hb-light,draft-simple,resonance-analyst --count 1
```

Optional stack roles:

```bash
export LYGO_STACK_ROOT=/absolute/path/to/lygo-protocol-stack
```

## Security (v0.6.0)

Read **before** install:

- `references/SECURITY.md`
- `references/SECURITY_AUDIT.md`
- `references/SKILLSPECTOR_AUDIT.md`
- `references/AGENT_CONTRACT.md`

| Gate | Purpose |
|------|---------|
| `LYGO_STACK_ROOT` | Your stack clone for stack-touching roles |
| `LYGO_ARMY_FULL_CAPACITY=1` | Full-capacity PS1 only (operator shell outside skill Python) |
| `LYGO_ARMY_SEED_TASKS=1` | Seed scripts |
| `LYGO_ARMY_IDLE_GUARDIAN=1` | Idle guardian supervisor |
| Planting `enabled` + consent | Egg/registry planter roles |

**Agents:** propose queue JSON only; never enable planting, full-capacity, or seed without explicit user request.

## Companion

LYGO RESONANCE: https://deepseekoracle.github.io/Excavationpro/LYGORESONANCE.html

## Version history

| Ver | Change |
|-----|--------|
| 0.5.0 | Declared permissions, webhook double-gate |
| **0.6.0** | **No process spawn** (runpy + threads); **no outbound webhook**; honest description; local alerts |

**Δ9Φ963 — local flame, reviewed queue, allowlisted tools, no silent outbound.**
