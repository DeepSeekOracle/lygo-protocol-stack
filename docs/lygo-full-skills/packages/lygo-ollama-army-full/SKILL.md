---
name: lygo-ollama-army
description: "Local Ollama multi-role army (in-process threads) + reviewed task queue. Strict basename allowlist under skill + LYGO_STACK_ROOT/tools (in-process runpy, no shell/OS process spawn). Localhost Ollama. Public HTTPS probes OFF unless sentinel.probe_public_pages=true. Social/planting roles OFF unless config consent flags. Local alerts JSONL only. No webhook, no remote LLM, no git/HF/ClawHub publish. Read references/SECURITY.md first."
version: 0.8.0
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
  consent_required: true
  version: "0.8.0"
  security_audit: "skillspector-2026-07-29-v0.8.0"
  signature: "Δ9Φ963-ARMY-SKILL-v0.8.0"
  publisher: deepseekoracle
  permissions_declared:
    filesystem: "army_workspace_and_optional_validated_LYGO_STACK_ROOT"
    os_process_spawn: false
    shell: false
    in_process_runpy: "allowlisted basenames only"
    network_default: "127.0.0.1_ollama"
    network_optional: "public_https_get_only_if_sentinel_probe_flags_true"
    outbound_webhook: false
    remote_llm: false
    social_autopublish: false
    git_push: false
    hf_write: false
    clawhub_publish: false
---

# LYGO Ollama Army & Assistant Hub v0.8.0

**Local Ollama automation** for a queue-driven light-model army on a trusted LYGO stack.

## Execution model (honest)

| Mechanism | Meaning |
|-----------|---------|
| **OS process spawn / shell** | **Never** (`subprocess` not used) |
| **In-process `runpy`** | Allowed only for **named** scripts in `ARMY_SCRIPT_ALLOW` / `STACK_TOOL_ALLOW` |
| **Daemon threads** | Multi-role workers inside one Python process |
| **Task queue** | JSON files you write; roles still **config-gated** (injection cannot enable social/planting alone) |

## Honest capability surface

| Surface | Default | Network |
|---------|---------|---------|
| Multi-role army (threads) | On when you launch | `127.0.0.1:11434` Ollama |
| Task queue | You drop JSON | None |
| Genesis console | Optional | **127.0.0.1 only** (metadata warning) |
| Sentinel | Ollama + queue + optional stack lattice | Stack tools if `LYGO_STACK_ROOT` set |
| Public page / HF probes | **OFF** | Only if `sentinel.probe_*=true` **and** task/role allowed |
| Planting / registry | **OFF** | `planting.enabled` + `consent` |
| Social / Moltx / Moltbook roles | **OFF** | `access.social_publish=true` |
| Heavy stack roles (audit/mesh/anchor/boot) | **OFF** | `access.allow_privileged_roles=true` |
| Webhook / Telegram | **Not supported** | Local `logs/alerts.jsonl` |
| git / HF / ClawHub publish | **Never** | — |

## Strict allowlist + role gates (v0.8.0)

`_safe_invoke.allowed_script` only permits **named** basenames (no wildcard `.py`).  

Daemon **also** refuses roles unless config allows them (see surface table).  

**Heartbeats ONLY** runs `sentinel_heartbeat.py` alone (no genesis collector).  

**Seed / idle cron** never enqueue `public-pages-check` unless `LYGO_ARMY_SEED_PUBLIC_PAGES=1` **and** probe flag true.

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

Optional stack (trusted clone only):

```bash
export LYGO_STACK_ROOT=/absolute/path/to/lygo-protocol-stack
```

## Agents

- Propose queue task JSON; human reviews before write.  
- Do **not** enable planting, social roles, public probes, or self_tune without explicit user request.  
- Do **not** set webhook/Telegram env vars (ignored / not shipped).  

## Security docs

- `references/SECURITY.md`  
- `references/SECURITY_AUDIT.md`  
- `references/SKILLSPECTOR_AUDIT.md`  

## Version history

| Ver | Change |
|-----|--------|
| 0.6.0 | No process spawn; no webhook HTTP |
| 0.7.0 | Strict allowlists; local-first defaults |
| **0.8.0** | Config-gated roles; no default public-pages seed; pure heartbeats; no hard-coded authority root; planting consent parity; genesis warning; no installer chaining |

**Δ9Φ963 — local Ollama · strict allowlist · opt-in stack · local alerts · no silent outbound.**
