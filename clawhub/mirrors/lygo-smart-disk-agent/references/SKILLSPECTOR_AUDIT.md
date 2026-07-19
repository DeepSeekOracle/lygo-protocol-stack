# SkillSpector / ClawHub security audit notes — lygo-smart-disk-agent

**Version:** 1.0.2  
**Signature:** `Δ9Φ963-LYGO-SMART-DISK-AGENT-v1.0.2`

## Scanner findings addressed

| Code | Severity | Location (1.0.0) | Resolution in 1.0.2 |
|------|----------|------------------|---------------------|
| `suspicious.dynamic_code_execution` | Critical | `scripts/self_check.py:22` (`importlib.exec_module`) | Removed. Self-check uses **static imports** only (`from kernel …`, `from agent …`). |
| `suspicious.install_untrusted_source` | Warn | `public/config/smart_disk.json:5` raw IP in URL | `ollama_base` is now `http://localhost:11434` (hostname, not raw IP). Bind is `localhost`. |

## Human-review summary (agentic risk)

The product is a **disclosed local offline agent**:

| Surface | Mitigation |
|---------|------------|
| No-login loopback portal | **By design** for USB one-shot; bind **localhost only**; refuse `0.0.0.0` unless `LYGO_SDA_ALLOW_LAN=1` |
| Stored chats | Full JSONL local only; **HTTP `/api/memory` returns previews** (80-char), not full dump |
| Host actions (`open-url`) | **Disabled over HTTP API**; CLI-only + allowlisted HTTPS/localhost prefixes |
| CORS | Wildcard CORS **removed** (same-origin portal) |
| POST bodies | Hard cap **64 KiB** |
| P0 | Input quarantine patterns + size cap |
| Secrets | No API keys or cloud credentials in package |
| Models | Weights not shipped; host Ollama only |

## Install trust

- Canonical source: https://github.com/DeepSeekOracle/lygo-protocol-stack/tree/main/lygo_smart_disk  
- ClawHub: `deepseekoracle/lygo-smart-disk-agent`  
- Do **not** install from third-party mirrors or shortener links.

## VirusTotal

ClawHub may attach VT after publish. Package is pure Python/HTML/JSON (no binaries). Expect clean once scanned.

## Operator consent

Installing this skill means you accept a **local open control plane** on your machine when you run the portal. Do not expose port 9631 to the network.

**Δ9Φ963 — static load · localhost · human review OK.**

