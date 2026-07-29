# SkillSpector — lygo-ollama-army v0.7.0 response

Prior audit (v0.6.0): 42 findings — allowlist bypass, description mismatch (webhook/social/GH/HF), drive scan, cross-skill cron, Discord ops launcher, external memory writes.

## Remediation

| Finding | Fix |
|---------|-----|
| Allowlist bypass (`any .py`) | Strict `ARMY_SCRIPT_ALLOW` + `STACK_TOOL_ALLOW` basenames only |
| Webhook docs / config | Removed; local `alerts.jsonl` only |
| Social cron / moltx seed | Removed from `army_cron_once` |
| Cross-skill token_saver path | Removed |
| Genesis GH/HF/drive scan/Discord | Collector rewritten local-only |
| Lightfather Discord desktop launcher | Removed from package |
| Sentinel remote probes default on | Default **off** |
| Health mutates queue | Read-only unless flags |
| Idle external LYRA_CORE writes | Gated `allow_external_memory_write` (default false) |
| Self-tune enables network probes | No longer auto-enables |
| Hardcoded I:\ paths in installers | `$PSScriptRoot` / env |
| Description mismatch | Honest SKILL.md network table |

Signature: `Δ9Φ963-ARMY-SKILLSPECTOR-v0.7.0`
