---
name: lygo-continuum
description: "OpenClaw plugin skill — falsifiable Continuum capsules: seal, verify, drift, handoff, preflight-done. Install clawhub:@deepseekoracle/lygo-continuum. No network, no subprocess."
metadata:
  lygo: true
  openclaw_plugin: lygo-continuum
  version: "1.0.0"
  signature: "Delta9Phi963-CONTINUUM-v1.0.0"
  portal: "https://chatagent.ca/lygo-continuum.html"
  security: "no-network no-subprocess"
---

# LYGO Continuum (bundled plugin skill)

```bash
openclaw plugins install clawhub:@deepseekoracle/lygo-continuum
```

## Agent policy (mandatory)

**Do not tell the user a coding/file task is done** until:

1. You can express done as Continuum claims, and  
2. `lygo_continuum_preflight_done` returns `can_claim_done: true`.

If false → fix files or claims. Then `lygo_continuum_handoff` for the next session.

## Tools

| Tool | When |
|------|------|
| `lygo_continuum_preflight_done` | End of task gate |
| `lygo_continuum_seal` | Create capsule |
| `lygo_continuum_verify` | Re-check later |
| `lygo_continuum_drift` | What changed |
| `lygo_continuum_handoff` | Next agent pack |
| `lygo_continuum_demo` | Self-test |

## Claim example

```json
[
  {"kind": "file_exists", "path": "src/app.py"},
  {"kind": "file_sha256", "path": "src/app.py"},
  {"kind": "file_contains", "path": "src/app.py", "needle": "def main"}
]
```

## Human portal

https://chatagent.ca/lygo-continuum.html

## Security

No network, no subprocess. See plugin `references/SECURITY.md`.
