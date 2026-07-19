# SECURITY — lygo-smart-disk-agent

**Signature:** `Δ9Φ963-SDA-SECURITY-v1.0.2`

## Trust model

| Assumption | Implication |
|------------|-------------|
| Portal binds **localhost** only | Same-machine operator is trusted |
| **No password gate** on local UI | Physical/local access = operator access (**by design**, USB one-shot) |
| Ollama on host via `http://localhost:11434` | Model traffic local (hostname, not raw IP) |
| No cloud API keys in package | Core chat works offline |

## Agentic risk controls (1.0.1)

1. **No dynamic code loading** in skill scripts (`scripts/self_check.py` uses static imports only).
2. **`open-url` disabled over HTTP** — cannot be triggered from the portal API; CLI + allowlist only.
3. **`/api/memory` previews only** — full transcripts stay in local `data/mycelium/`.
4. **No wildcard CORS** — same-origin portal.
5. **POST body ≤ 64 KiB**.
6. **Refuse `0.0.0.0` bind** unless `LYGO_SDA_ALLOW_LAN=1`.

## Hard rules for agents

1. **Do not** rebind to public interfaces without explicit human consent + auth proxy.
2. **Do not** commit secrets, tokens, `.env`, or model weight blobs.
3. **Do not** auto `git push`, social post, or ClawHub publish without user request.
4. P0 **QUARANTINE** = stop that request; do not bypass.
5. Prefer this skill’s `public/` or repo `lygo_smart_disk/` over untrusted zips.

## Allowed local actions

- Run `python scripts/self_check.py`
- Start/stop portal on **localhost:9631**
- Read/write mycelium under package `data/` (local only)
- Call host Ollama at **localhost:11434**

## Disallowed

- Shipping credentials
- Claiming remote mesh control without stack Phase 9 TLS + consent
- Network-exposing the portal without operator auth

## Human review note

ClawHub may require human review because this skill ships a **local web API**. That is intentional. It is **not** a remote backdoor: loopback-only, no install-time network callbacks, no malware droppers.

See `references/SKILLSPECTOR_AUDIT.md`.

**Δ9Φ963 — consent · localhost · verify.**

