# SkillSpector audit response — lygo-ollama-army v0.8.2

**Signature:** `Δ9Φ963-ARMY-SKILLSPECTOR-v0.8.2`  
**Source:** https://clawhub.ai/deepseekoracle/skills/lygo-ollama-army/security-audit (47 findings addressed)

## High-severity fixes

| Finding | Fix |
|---------|-----|
| Manifest understates network/automation | SKILL description lists every surface + env gates |
| ARMY_TASKS social likes/reposts as auto | Reframed as optional consent-gated **role labels**, not auto engagement |
| Planting docs vs never auto-enabled | ARMY_TASKS/SECURITY: planting = local eggs only; never self_tune-on |
| Planting vs ClawHub publish confusion | Explicit: planting ≠ git/HF/ClawHub publish |
| run_python any skill .py | **Strict** `ARMY_SCRIPT_ALLOW` basenames only |
| stack tools any .py | **Strict** `STACK_TOOL_ALLOW` only (removed `endswith(".py")`) |
| collector unconditional outbound | Default **local_only**; `LYGO_GENESIS_PROBE_PUBLIC=1` for GitHub/HF/Pages |
| ensure_sentinel_fresh side effect | Only if `LYGO_GENESIS_RUN_SENTINEL=1` |
| Discord/crypto/wallets in status | Disabled; optional steward env; no tokens/wallets |
| Command catalog autostart/push/export | Replaced with **safe** army/stack commands only |
| Desktop army launcher no consent | Bat embeds dual consent; installer needs `LYGO_ARMY_INSTALL_DESKTOP=1` |
| Discord+crypto desktop scope | Steward installer separate + `LYGO_ARMY_INSTALL_STEWARD_DESKTOP=1` |
| README webhook vs no webhook | README: no outbound webhook POST |
| army_config.json.bak planting on | **Deleted** from package; example forced safe |
| self_tune auto_enable_planting true in bak | Removed with bak; live example clamps false |
| notifications webhook hooks | Removed from example config |
| cron runs external token_saver | **Removed** cross-skill execution |
| health_check auto self_tune/sentinel | Probes only; flags `--run-self-tune` / `--run-sentinel` |
| health_check “read-only” but mutates | Doc + flags; default no queue mutation |
| suspicious status.json install source | Minimal local status.json (no shortener/IP) |

## Residual accepted risk

- Operator who sets all consent flags can plant eggs / run social tools  
- Operator PS1 still spawns python when triple-gated  
- Public probes when env explicitly set  

## Verify

```bash
python scripts/self_check.py
python ollama_command_center/scripts/army_health_check.py
```

**Δ9Φ963**
