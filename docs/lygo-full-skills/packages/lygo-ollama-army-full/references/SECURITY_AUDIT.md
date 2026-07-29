# SkillSpector / ClawHub response — lygo-ollama-army v0.6.0

**Date:** 2026-07-29  
**Prior findings (v0.5.0):** 72 findings — process spawn, taint flows, webhook Critical, description mismatch.

## Remediation summary

| Finding class | v0.5.0 | v0.6.0 |
|---------------|--------|--------|
| `subprocess.run` / `Popen` | Widespread | **Removed** — `_safe_invoke.run_python` (runpy) + `run_daemon_thread` |
| Env → process spawn taint | script path / env | **N/A** — no process spawn |
| Env → webhook `urlopen` (Critical) | Double-gated still present | **Removed** — `write_local_alert` → `logs/alerts.jsonl` only |
| Git CLI spawn | `git status` | **Filesystem** `git_status_summary` |
| Description mismatch (Tp4) | Marketed as simple local | **Honest** surface table in SKILL.md (threads, stack tools, localhost dashboard, local alerts) |
| Shell / `cmd /k` windows | Opt-in visible | **Removed** — `--visible-windows` no-op |

## Function preserved

- Multi-role army (threaded daemons)  
- Queue + results  
- Champion personas + resonance-analyst  
- Stack roles via allowlisted in-process tools  
- Sentinel, idle guardian, self-tune, planting **gates** (consent)  
- Genesis localhost dashboard  

## Residual accepted surface

- HTTPS GET to operator-configured **public** lattice URLs (sentinel page probe)  
- HTTP client to `127.0.0.1:11434` (Ollama)  
- Filesystem under army folder + validated stack root  

## Operator verify

```bash
python -c "import pathlib; import re; root=pathlib.Path('.');
assert not any(re.search(r'import subprocess', p.read_text(encoding='utf-8',errors='replace')) for p in root.rglob('*.py') if p.name!='_safe_invoke.py' or True);
print('ok')"
python ollama_army_launcher.py --help
python ollama_command_center/scripts/sentinel_heartbeat.py
```

**Δ9Φ963 — disclose · gate · local-first · no silent outbound.**
