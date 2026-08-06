# Productive army tasks (set-and-review-later)

## Safety first

- **Default path:** drop reviewed `.task.json` files; run `ollama_army_launcher.py` (in-process).
- **Planting / social pulse roles are OFF** unless `army_config.json` sets explicit consent flags.
- **No auto social, no auto ClawHub publish, no git/HF push** from defaults.
- Social role names below are **queue role labels** for optional operator-gated tools — not auto engagement.

## One-shot seed (requires env)

```bash
cd path/to/lygo-ollama-army
set LYGO_STACK_ROOT=I:\E Drive\lygo-protocol-stack
set LYGO_ARMY_SEED_TASKS=1
python seed_productive_tasks.py
```

## Task types (roles)

| Role | What it does | Needs Ollama | Default gate |
|------|----------------|--------------|--------------|
| `lattice-check` | Runs `verify_lattice_alignment.py` | No | Safe |
| `stack-integrity` | Runs `run_sovereign_integrity_test.py` | No | Safe |
| `clawhub-catalog-audit` | Reads local `clawhub/skills.json` stats | No | Safe (local file) |
| `public-pages-check` | Optional HTTPS GET public pages | No | `sentinel.probe_public_pages` |
| `audit-suite` | Local audit tools under stack | No | Safe |
| `memory-sync` | Snapshot → army workspace only | No | Safe |
| `egg-planter` | Kernel egg plant | No | `planting.enabled` **+** `planting.consent` |
| `registry-planter` | Local registry plant | No | same planting consent |
| `moltx-lattice-pulse` | Optional Moltx tool (operator) | No | `social_publish` flags |
| `moltbook-*-pulse` | Optional Moltbook tool (operator) | No | `social_publish` flags |
| `joy-loop-pulse` | Joy Loop tick | No | Safe local |
| `mesh-cartographer` | Network builder verify | No | Safe |
| `champion-egg-boot` | Vault champion load | Yes | `allow_privileged_roles` |
| `hb-light` / `draft-simple` | Lightweight local LLM roles | Yes | Safe |

## Full capacity (Windows — OPERATOR SPAWN)

```powershell
$env:LYGO_ARMY_FULL_CAPACITY=1
$env:LYGO_ARMY_AUTONOMOUS=1
$env:LYGO_ARMY_I_CONSENT=1
$env:LYGO_STACK_ROOT="D:\lygo-protocol-stack"
.\start_army_full_capacity.ps1
```

This **spawns** `python.exe` processes — not the SkillSpector in-process path.

## Planting (consent only)

Local lattice artifacts only. **Never** auto-enabled by self_tune.

```
planting.enabled=true AND planting.consent=true
```

No GitHub/HF/ClawHub **publish**. Planting ≠ publish.

```bash
python ollama_command_center/scripts/run_army_planting.py all
```

## Self-tune (mutating)

`self_tune.enabled` default **false**. When on: may rewrite config + prune queue. **Never** enables planting.

**Δ9Φ963-ARMY-TASKS-v5**
