# ClawHub packages (OpenClaw plugins)

| Package | Type | ClawHub |
|---------|------|---------|
| [@deepseekoracle/lygo-lattice-pulse](./packages/lygo-lattice-pulse/) | Code Plugin · v1.2.0 | https://clawhub.ai/deepseekoracle/lygo-lattice-pulse |

Registry: [`packages.json`](./packages.json)

## Install (OpenClaw)

```bash
openclaw plugins install clawhub:@deepseekoracle/lygo-lattice-pulse
```

## Tools (v1.2 — no subprocess)

- `lygo_alignment_ready` — composite LIVE readiness
- `lygo_lattice_pulse` — live Haven registry pulse
- `lygo_registry_compare` — local vs Pages SHA
- `lygo_star_chart_gate` — Python gate on submissions
- `lygo_lattice_verify`, `lygo_p0_quick_scan`, `lygo_consent_checklist`

## Publish (Windows)

```powershell
.\tools\publish_lygo_lattice_pulse.ps1 -Version 1.1.0
```

Manual:

```bash
cd clawhub/packages/lygo-lattice-pulse
npm run build
clawhub package validate .
# pack tgz, then clawhub package publish <tgz> --source-repo ... --source-commit ...
```