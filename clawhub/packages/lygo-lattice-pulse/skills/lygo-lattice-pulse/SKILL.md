---
name: lygo-lattice-pulse
description: "Use OpenClaw lygo-lattice-pulse plugin tools — live Haven heartbeat, stack verify, P0 quick-scan, consent checklist before LYGO live writes."
metadata: {"lygo": true, "openclaw_plugin": "lygo-lattice-pulse", "version": "1.0.0"}
---

# LYGO Lattice Pulse (plugin skill)

Bundled with **@deepseekoracle/lygo-lattice-pulse** OpenClaw plugin.

## When to use

- Before claiming LIVE lattice status — run **`lygo_lattice_pulse`**
- Before star chart submit/ingest — run **`lygo_consent_checklist`**
- After cloning stack — run **`lygo_lattice_verify`**
- Before public posts with LYGO math/seals — run **`lygo_p0_quick_scan`**

## Tool quick reference

```
lygo_lattice_pulse()           → live registry SHA, nodes, galaxies, feed tail
lygo_lattice_verify()          → LYGO_STACK_ROOT marker checks
lygo_p0_quick_scan({ text })   → AMPLIFY / NEUTRAL / QUARANTINE heuristic
lygo_consent_checklist()       → --i-consent workflow + skill chain
```

## Config

Set `plugins.entries.lygo-lattice-pulse.config.stackRoot` or export `LYGO_STACK_ROOT`.

## Not a substitute for

Authoritative gates still run in Python: `haven_star_chart_gate.py`, `verify_lattice_alignment.py`, stack P0 filter.