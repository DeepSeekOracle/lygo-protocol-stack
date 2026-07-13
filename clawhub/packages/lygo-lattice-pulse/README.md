# @deepseekoracle/lygo-lattice-pulse

**Δ9Φ963** · LYGO lattice **OpenClaw plugin** — live Haven heartbeat, stack verification, registry alignment, and star chart gate integration.

**ClawHub:** https://clawhub.ai/deepseekoracle/lygo-lattice-pulse

## Install

```bash
openclaw plugins install clawhub:@deepseekoracle/lygo-lattice-pulse
```

## Tools (v1.2 — SkillSpector-safe)

| Tool | Purpose |
|------|---------|
| `lygo_alignment_ready` | Composite readiness score before live ops |
| `lygo_lattice_pulse` | Live Haven registry + feed pulse |
| `lygo_registry_compare` | Local vs Pages SHA256 match |
| `lygo_lattice_verify` | Stack marker audit (read-only; no subprocess) |
| `lygo_star_chart_gate` | JS gate **preview** on submission JSON |
| `lygo_p0_quick_scan` | Fast text heuristic |
| `lygo_consent_checklist` | Human consent workflow |

**Authoritative gate (terminal):** `python scripts/gate_submission.py <submission.json>` with `LYGO_STACK_ROOT` set.

## Security (v1.2)

- **No `child_process`** in plugin runtime — addresses SkillSpector `suspicious.dangerous_exec`.
- See `references/SKILLSPECTOR_AUDIT.md`.

## Build

```bash
npm run build   # esbuild → dist/index.js
clawhub package validate .
```

## Publish (maintainers)

```powershell
.\tools\publish_lygo_lattice_pulse.ps1 -Version 1.2.0
```

## License

MIT-0