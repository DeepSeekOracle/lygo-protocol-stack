# SECURITY — lygo-smart-disk-agent

**Signature:** `Δ9Φ963-SDA-SECURITY-v1`

## Trust model

| Assumption | Implication |
|------------|-------------|
| Portal binds **127.0.0.1** only | Same-machine user is trusted |
| **No password gate** on local UI | Physical/local access = operator access (by design) |
| Ollama on host | Model traffic stays local unless user reconfigures Ollama |
| No cloud API keys in package | Core chat works offline |

## Hard rules for agents

1. **Do not** rebind to `0.0.0.0` or public interfaces without explicit human consent + auth proxy.
2. **Do not** commit secrets, tokens, `.env`, or model weight blobs.
3. **Do not** auto `git push`, social post, or ClawHub publish without user request.
4. P0 **QUARANTINE** = stop that request; do not bypass with flags.
5. Skill `public/` is the portable product — prefer it or repo `lygo_smart_disk/` over random forks with unknown binaries.

## Allowed local actions

- Run `verify/self_check.py` and unit tests
- Start/stop portal on loopback
- Read/write mycelium under package `data/` (local only)
- Call host Ollama at `127.0.0.1:11434`

## Disallowed

- Shipping credentials in SKILL.md or config
- Claiming remote mesh control without stack Phase 9 TLS + consent
- Impersonating OpenClaw vendor branding as this product

## Firmware lineage (public, no secrets)

- https://deepseekoracle.github.io/Excavationpro/LYGO-Network/Ethical-Chip-FirmwareV2.html
- https://deepseekoracle.github.io/Excavationpro/LYGO-Network/LYGOGUARDIAN.html

**Δ9Φ963 — consent · loopback · verify.**
