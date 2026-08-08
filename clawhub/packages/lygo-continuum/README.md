# @deepseekoracle/lygo-continuum

**OpenClaw code plugin** — falsifiable work capsules for AI agents.

Agents say “done.” Continuum makes that claim **checkable**: seal file hashes / contains / JSON paths → re-verify later → detect **drift** → emit a **handoff pack**.

| Surface | Link |
|---------|------|
| ClawHub | `clawhub:@deepseekoracle/lygo-continuum` |
| Human portal | https://chatagent.ca/lygo-continuum.html |
| Guide | https://chatagent.ca/guides/ai-agent-done-claims-continuum.html |
| Signature | `Delta9Phi963-CONTINUUM-v1.0.0` |

## Install

```bash
openclaw plugins install clawhub:@deepseekoracle/lygo-continuum
```

## Tools

| Tool | Purpose |
|------|---------|
| `lygo_continuum_preflight_done` | **Call before saying done** — seal + verify; `can_claim_done` |
| `lygo_continuum_seal` | Build capsule from claims JSON |
| `lygo_continuum_verify` | Re-check capsule vs disk |
| `lygo_continuum_drift` | Slim drift report |
| `lygo_continuum_handoff` | Markdown pack for next agent |
| `lygo_continuum_kinds` | Claim kind catalog |
| `lygo_continuum_demo` | Self-test (seal→hold→tamper→drift) |

## Security

- **No network** in plugin runtime  
- **No subprocess / shell**  
- Filesystem read only for claim paths under `base` / cwd  
- No auto git push or social publish  

See `references/SECURITY.md`.

## Build

```bash
cd clawhub/packages/lygo-continuum
npm install typebox@1.1.39 --no-save
npx esbuild src/index.ts --bundle --platform=node --format=esm \
  --external:openclaw/plugin-sdk/plugin-entry --external:typebox \
  --outfile=dist/index.js
npx clawhub package validate .
```

## License

MIT-0
