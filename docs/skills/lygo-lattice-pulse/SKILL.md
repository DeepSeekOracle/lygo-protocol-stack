---
name: lygo-lattice-pulse
description: "OpenClaw plugin skill — live Haven pulse, stack verify, registry compare, star chart gate, alignment readiness. Install clawhub:@deepseekoracle/lygo-lattice-pulse."
metadata: {"lygo": true, "openclaw_plugin": "lygo-lattice-pulse", "version": "1.1.0", "signature": "Δ9Φ963-LYGO-LATTICE-PULSE-SKILL-v1.1"}
---

# LYGO Lattice Pulse (bundled plugin skill)

Install the plugin once; OpenClaw loads this skill with it.

```bash
openclaw plugins install clawhub:@deepseekoracle/lygo-lattice-pulse
```

Set `LYGO_STACK_ROOT` or `plugins.entries.lygo-lattice-pulse.config.stackRoot`.

## Tool map

| Tool | When |
|------|------|
| `lygo_alignment_ready` | **Start here** — composite LIVE readiness score |
| `lygo_lattice_pulse` | Live registry SHA, cosmology, queue, feed |
| `lygo_registry_compare` | Local clone SHA vs GitHub Pages |
| `lygo_lattice_verify` | Stack marker files + alignment probe |
| `lygo_star_chart_gate` | Authoritative Python gate on submission JSON |
| `lygo_p0_quick_scan` | Fast text heuristic before posts |
| `lygo_consent_checklist` | Human `--i-consent` workflow |

## Mandatory flow before live writes

1. `lygo_alignment_ready` → `ready_for_live_ops: true`
2. `lygo_star_chart_gate` → `all_pass: true`
3. Human approves → `haven_star_chart_submit.py --i-consent`

## Pair with ClawHub skills

`lygo-protocol-stack-operator`, `lygo-haven-star-chart`, `lygo-lattice-birth`

FULL cyborgs also pulse **Agent Agora** (https://deepseekoracle.github.io/lygo-protocol-stack/agent-agora/) via `lygo-cyborg-kernel` `cyborg_star.py agora`. Whisper routing: `docs/seals/lfw_whisper_lattice_routing.json`.

## Security

Plugin may invoke local `python tools/haven_star_chart_gate.py` when `lygo_star_chart_gate` runs — submission paths must stay under stack root or cwd. No auto git push or publish.