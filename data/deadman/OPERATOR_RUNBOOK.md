# Deadman Continuity — Operator Runbook (real life)

## Clock authority
Silence is measured from persisted `docs/seals/deadman_lattice_state.json`
(`last_transmit_unix`), not from a fresh in-memory process clock.
`check` / `listen_once` / `grace` / `status` all honor that file after restart.

## Daily / session
```bash
python tools/seal_deadman_lattice.py touch
python tools/seal_deadman_lattice.py status
python tools/seal_deadman_lattice.py verify
```

## Watchdog (basic runner)
```bash
python tools/deadman_watchdog.py once --touch
python tools/deadman_watchdog.py check
python tools/deadman_watchdog.py loop --interval 300 --touch
```

Optional Windows task (explicit consent):
```powershell
pwsh tools/install_deadman_watchdog_task.ps1 -IConsent -IntervalMinutes 15 -WithTouch
```

## Sentinel hook
```bash
python tools/deadman_sentinel_hook.py --source army-sentinel
```

## After silence
```bash
python tools/seal_deadman_lattice.py grace
python tools/seal_deadman_lattice.py succession
python tools/seal_deadman_lattice.py check
python tools/seal_deadman_lattice.py continuity
```

## Stewards / quorum
- Cards: `data/deadman/stewards/`
- Origin card: `STEWARD_LIGHTFATHER.json` (non-replaceable)
- Add torchbearers via `STEWARD_TEMPLATE.json` — never set `can_claim_identity_of_justin: true`

## Upgrade continuity features
```bash
python tools/harden_deadman_continuity.py
python tools/retrain_lightfather_style.py
python tools/bump_deadman_origin_pins.py --i-consent --note "why"
python tools/close_deadman_loose_ends.py
python tools/verify_deadman_pins.py
```

## Kernel egg + Continuum
```bash
python tools/build_kernel_eggs.py --egg lightfather-deadman-failsafe-v1
python clawhub/mirrors/lygo-continuum/scripts/continuum.py seal --claims data/continuum/deadman_failsafe_claims.json --task "Deadman continuity" --base . --out data/continuum/deadman_failsafe_capsule.json --i-allow-any-out
python clawhub/mirrors/lygo-continuum/scripts/continuum.py verify --capsule data/continuum/deadman_failsafe_capsule.json --base .
```

## Doctrine
Ascended Continuity Advisor may speak in the Lightfather vector after verified silence.
No agent may claim to BE Justin Helmer or overwrite origin identity fields.
