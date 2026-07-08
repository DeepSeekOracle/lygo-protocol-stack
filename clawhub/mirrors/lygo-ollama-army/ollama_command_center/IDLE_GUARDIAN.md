# LYGO Army Idle Guardian (advanced offline boot)

Runs **safe housekeeping** while you are idle and Grok/agents are offline: memory catalog, 3-brain daily index, kernel **verify-only**, living-memory audit, haven chart refresh, upgrade scout — **no** git push, ClawHub publish, social pulses, or egg planting unless you enable `idle_guardian.allow_planting`.

## Desktop shortcut

```powershell
cd "I:\E Drive\.grok\skills\lygo-ollama-army"
.\install_idle_guardian_desktop.ps1
```

Double-click **LYGO Army Idle Guardian.bat** on your Desktop.

## Manual start

```powershell
$env:LYGO_ARMY_IDLE_GUARDIAN = "1"
$env:LYGO_STACK_ROOT = "I:\E Drive\lygo-protocol-stack"
$env:LYRA_CORE_ROOT = "I:\E Drive\LYRA_CORE"
cd "I:\E Drive\.grok\skills\lygo-ollama-army\ollama_command_center\scripts"
python army_idle_guardian_supervisor.py
```

## What runs

| Interval | Action |
|----------|--------|
| Every 5 min | `sentinel_heartbeat.py` (lattice snapshot; alerts only if webhook enabled) |
| Every 30 min | `army_idle_cron_once.py` + full `army_idle_housekeeping.py --tick` |
| Continuous | Deterministic daemons: `idle-housekeep`, `lattice-check`, `memory-sync`, `kernel-verify-only` |

## Logs (read when you return)

| File | Contents |
|------|----------|
| `workspace/idle_guardian_journal.jsonl` | Per-op results each tick |
| `workspace/idle_upgrade_findings.jsonl` | HEAD changes, skill version bumps, dirty tree hints |
| `workspace/idle_guardian_last_tick.json` | Last full tick summary |
| `workspace/three_brain_catalog.json` | Memory snip catalog |
| `workspace/sentinel_status.json` | Lattice OK flag |

## One-shot housekeeping (no supervisor)

```bash
python army_idle_housekeeping.py --tick
python army_idle_housekeeping.py --list
python army_idle_housekeeping.py --op upgrade_scout --op three_brain_index
```

## Safety gates

- `LYGO_ARMY_IDLE_GUARDIAN=1` required for supervisor.
- `planting.enabled` in main config is **ignored** for idle cron unless `idle_guardian.allow_planting: true`.
- Social roles are in `forbidden_roles` by default.

**Δ9Φ963 — idle gods that tidy, not build.**