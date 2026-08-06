# SkillSpector audit response — lygo-ollama-army v0.8.1

**Signature:** `Δ9Φ963-ARMY-SKILLSPECTOR-v0.8.1`

## NVIDIA findings (ClawHub outstanding) → fixes

| Finding | Severity | Fix in 0.8.1 |
|---------|----------|--------------|
| Description understates dashboard / HTTPS probes / browser / roles | High | SKILL frontmatter lists **full honest surface**; browser only if `LYGO_GENESIS_OPEN_BROWSER=1` |
| Supervisor overbroad cron/plant messaging | Medium | Banner lists consent gates; cron seeds safe roles only; plant needs enabled+consent |
| idle allow_planting vs external memory | Medium | Flags independent; plant-like op names refused when `allow_planting=false`; external write separate |
| self_tune auto_enable_planting | High | **Never enables planting**; forces `auto_enable_planting=false` + `allow_auto_enable=false` every write |
| self_tune “read-only” mismatch | Medium | Docstring + report `mutating: true` + honest_surface text |
| PS1 expands beyond reviewed queue | Medium/High | PS1 documented as OPERATOR-ONLY process spawn; triple env gate; optional one-shots off |
| PS1 process spawn vs no-spawn claim | High | Manifest splits Python skill vs PS1; PS1 header refuses mislabeling |
| Supervisor no confirmation | Medium | Requires `LYGO_ARMY_AUTONOMOUS=1` **and** `LYGO_ARMY_I_CONSENT=1` |

## Runtime split (reviewers)

| Path | Spawn | Gates |
|------|-------|-------|
| `ollama_army_launcher.py` | None (threads) | None beyond user run |
| `army_autonomous_supervisor.py` | None (threads + runpy) | AUTONOMOUS + I_CONSENT |
| `start_army_full_capacity.ps1` | **Yes** `python.exe` | FULL_CAPACITY + AUTONOMOUS + I_CONSENT + STACK_ROOT |
| `genesis_console/server.py` | None; optional browser | Localhost bind; OPEN_BROWSER env |

## Residual risk (accepted)

- Operator who sets all env gates + planting.consent can plant eggs  
- self_tune when enabled rewrites local config (documented)  
- Validated `LYGO_STACK_ROOT` runpy can run allowlisted stack tools  

## Operator checklist

1. Copy `army_config.example.json` → `army_config.json`  
2. Confirm planting/self_tune/social/probes all false  
3. Prefer `python ollama_army_launcher.py`  
4. Never set FULL_CAPACITY unless you accept OS process spawn  

**Δ9Φ963**
