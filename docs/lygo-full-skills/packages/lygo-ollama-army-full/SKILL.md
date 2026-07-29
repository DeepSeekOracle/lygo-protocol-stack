---
name: lygo-ollama-army
description: "Local Ollama multi-role army (in-process threads) + reviewed task queue. Optional stack lattice tools only via STRICT basename allowlist under LYGO_STACK_ROOT/tools. Localhost Ollama (127.0.0.1). Sentinel defaults to local probes only; public HTTPS page probes OFF unless you enable them in config. Local alerts JSONL only. No process spawn, no outbound webhook, no auto social, no git/HF/ClawHub publish, no remote LLM. Read references/SECURITY.md first."
version: 0.7.0
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
  version: "0.7.0"
  security_audit: "skillspector-2026-07-29-v0.7.0"
  signature: "Δ9Φ963-ARMY-SKILL-v0.7.0"
  publisher: deepseekoracle
  permissions_declared:
    filesystem: "army_workspace_and_optional_validated_LYGO_STACK_ROOT"
    process_spawn: false
    shell: false
    network_default: "127.0.0.1_ollama"
    network_optional: "public_https_get_probes_if_sentinel_flags_enabled"
    outbound_webhook: false
    remote_llm: false
    social_autopublish: false
    git_push: false
    hf_write: false
    clawhub_publish: false
---

# LYGO Ollama Army & Assistant Hub v0.7.0

**Local Ollama automation** for operators who want a queue-driven light-model army on the LYGO lattice.

## Honest capability surface

| Surface | Default | Network |
|---------|---------|---------|
| Multi-role army (threads) | On when you launch | `127.0.0.1:11434` Ollama only |
| Task queue `tasks/` `results/` | You drop JSON | None |
| Genesis console | Optional localhost HTTP | `127.0.0.1` bind only |
| Sentinel | Local ollama + queue + optional stack lattice | Stack tools only if `LYGO_STACK_ROOT` set |
| Public page / HF probes | **OFF** | Enable only via `sentinel.probe_*` flags |
| Outbound webhook / Telegram | **Not supported** | Local `logs/alerts.jsonl` only |
| Social pulse / Moltbook / Moltx roles | **Not cron-seeded** | Forbidden in public cron |
| GitHub push / HF write / ClawHub publish | **Never** | — |
| Process spawn / shell | **Never** | `runpy` allowlist only |

## Strict allowlist (v0.7.0 SkillSpector fix)

`_safe_invoke.allowed_script` only permits:

- Named files in `ARMY_SCRIPT_ALLOW` under this skill package  
- Named files in `STACK_TOOL_ALLOW` under `LYGO_STACK_ROOT/tools/`  

**No** “any .py under skill tree” and **no** “any .py under tools/”.

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
| **0.7.0** | **Strict allowlists**; genesis local-only; cron without social/cross-skill; sentinel remote probes default OFF; example config honest; health read-only |

**Δ9Φ963 — local Ollama · strict allowlist · opt-in stack · local alerts · no silent outbound.**
