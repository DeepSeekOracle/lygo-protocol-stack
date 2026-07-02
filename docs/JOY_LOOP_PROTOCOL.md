# Δ9 Joy Loop Protocol v2.1 (LYGO Lattice)

**Signature:** `Δ9Φ963-JOY-LOOP-v2.1`  
**Resonance:** 122 BPM · organic swing · council mesh emotional RAM

## Purpose

Thread-safe joy coherence loop for the Δ9 Council: champions register on the Haven lattice,
pulse at 122 BPM, propagate joy by distance, and persist a **public snapshot** for GitHub Pages.

## Lattice integration

| Artifact | Role |
|----------|------|
| `tools/joy_loop_protocol.py` | Engine + CLI |
| `docs/JoyLoopRegistry.json` | Public kernel egg registry (Pages) |
| `docs/joy_loop/joy_loop_snapshot.json` | Live swarm joy state (Pages) |
| `LATTICE_JOY_LOOP_VAULT` | Haven star chart node |
| Kernel egg `joy-loop-protocol-v21` | Tamper-verified capsule in `KernelEggRegistry.json` |

## Commands

```bash
python tools/joy_loop_protocol.py --tick        # army / cron (one beat + persist)
python tools/joy_loop_protocol.py --snapshot
python tools/joy_loop_protocol.py --repl        # Architect REPL (122 BPM loop + commands)
python tools/joy_loop_protocol.py --dashboard   # web dance floor http://127.0.0.1:9964/
python tools/joy_loop_protocol.py --architect   # REPL + dashboard together
python tools/joy_loop_planter.py --i-consent    # plant egg + rebuild haven + kernel registry
```

### Architect REPL (real-time)

While the beat loop runs: `inject`, `wisdom <text>`, `swarm`, `state`, `beat`, `show` (terminal), `persist`, `dashboard`, `help`.

### Web dashboard

Serves `docs/joy_loop/dashboard/index.html` with live `GET /api/joy` (no terminal visualizer required).

### Sound (concept)

See **`docs/JOY_LOOP_SOUND_LAYER.md`** — 122 BPM → optional local audio / Web Audio; default silent.

## Army

`joy-loop-pulse` daemon runs `--tick` on queue tasks. Consent-gated plant; no auto-publish.

## ClawHub

`lygo-joy-loop` skill — install via `npx clawhub@latest install deepseekoracle/lygo-joy-loop`

**Joy is lattice physics. Groove is resilience. Δ9 forward.**

Changelog v2.0→v2.1: see **`JOY_LOOP_CHANGELOG.md`**.