# Moltx posting — security

## Credentials (never in git)

| Location | Purpose |
|----------|---------|
| `%OPENCLAW_HOME%\credentials\moltx.json` | Canonical — `{"api_key": "moltx_sk_..."}` |
| `MOLTX_CREDENTIALS_PATH` | Override path (optional) |

**Not** `moltbook_sk_*` (different service). **Not** committed in `lygo-protocol-stack`.

## Scripts

| Tool | Gate |
|------|------|
| `tools/moltx_manual_post_once.py` | Requires `--i-consent`; redacts errors; receipt → `data/moltx/last_manual_post.json` |
| `tools/moltx_lattice_pulse.py` | Full engage session — maintainer only |

```bash
python tools/moltx_manual_post_once.py --dry-run --i-consent
python tools/moltx_manual_post_once.py --i-consent
python tools/moltx_manual_post_once.py --i-consent --file docs/MOLTX_GROK_HARNESS_REPLY.txt
```

## DNS / network

Posting needs resolve `moltx.io`. Agent sandboxes without DNS must run the script **on your machine**, not in remote harness.

Optional: `MOLTX_API_BASE` (default `https://moltx.io/v1`) — do not point at untrusted hosts.

## Receipts

`data/moltx/*.json` may contain post ids and redacted errors — add to `.gitignore` if you prefer (optional local-only).