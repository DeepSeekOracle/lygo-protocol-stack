# SkillSpector / ClawHub security audit — lygo-smart-disk-agent

**Version:** 1.0.3  
**Signature:** `Δ9Φ963-LYGO-SMART-DISK-AGENT-v1.0.3`

## Static analysis

| Status | Detail |
|--------|--------|
| **No suspicious patterns detected** | 1.0.1+ removed dynamic `exec_module`; config uses `localhost` not raw IP |

## Human-review gate (agentic risk)

### ClawHub overview (remaining concern)

> Disclosed local AI portal without authentication; risk of exposing stored chats via local HTTP limb interface.

### How 1.0.3 addresses that

| Concern | Control in 1.0.3 |
|---------|------------------|
| Unauthenticated portal | **Intentional** single-operator localhost product (USB one-shot). Bind **localhost only**; refuses `0.0.0.0` unless `LYGO_SDA_ALLOW_LAN=1`. Not a remote service. |
| Stored chats over HTTP limbs | **`memory` limb disabled over HTTP** (403). **`GET /api/memory` returns 403**. |
| Chat text on disk | Chats store **SHA-256 prefix + lengths only** — not full message/reply text. |
| Host actions | `open-url` still **HTTP-disabled**; CLI allowlist only. |
| Status path leak | `root` path **redacted** on HTTP status. |
| CORS / body size | No wildcard CORS; POST ≤ 64 KiB. |

### What remains open-by-design (disclose to reviewer)

- Interactive **chat** on `localhost:9631` has **no password** (same-machine operator = trusted).
- Do **not** install if you need multi-user OS isolation without a separate auth proxy.
- VirusTotal: pure Python/HTML/JSON package; no native binaries.

## Install trust

- Source: https://github.com/DeepSeekOracle/lygo-protocol-stack/tree/main/lygo_smart_disk  
- ClawHub: https://clawhub.ai/deepseekoracle/lygo-smart-disk-agent  
- Skill security: `references/SECURITY.md`

## Reviewer decision guide

| Decision | When |
|----------|------|
| **Approve** | Accept disclosed local open loopback agent with chat-memory **not** on HTTP |
| **Reject** | Policy requires login for any local agent UI (product is intentionally no-password) |

**Δ9Φ963 — static clean · chats off HTTP · localhost operator.**
