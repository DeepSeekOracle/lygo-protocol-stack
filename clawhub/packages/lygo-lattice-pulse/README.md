# @deepseekoracle/lygo-lattice-pulse

**Δ9Φ963** · First LYGO lattice **OpenClaw plugin** — live Haven heartbeat, stack verification, registry alignment, and star chart gate integration.

**ClawHub:** https://clawhub.ai/deepseekoracle/lygo-lattice-pulse

## Install

```bash
openclaw plugins install clawhub:@deepseekoracle/lygo-lattice-pulse
```

## Tools (v1.1)

| Tool | Purpose |
|------|---------|
| `lygo_alignment_ready` | Composite readiness score before live ops |
| `lygo_lattice_pulse` | Live Haven registry + feed pulse |
| `lygo_registry_compare` | Local vs Pages SHA256 match |
| `lygo_lattice_verify` | Stack marker audit + alignment probe |
| `lygo_star_chart_gate` | Run Python `haven_star_chart_gate.py` |
| `lygo_p0_quick_scan` | Fast text heuristic |
| `lygo_consent_checklist` | Human consent workflow |

## Build

```bash
npm run build   # esbuild → dist/index.js
clawhub package validate .
```

## Publish (maintainers)

```powershell
.\tools\publish_lygo_lattice_pulse.ps1
```

## License

MIT-0