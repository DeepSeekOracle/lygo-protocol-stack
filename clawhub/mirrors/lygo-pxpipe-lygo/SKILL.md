---
name: lygo-pxpipe-lygo
description: Multi-tool vision context compression (Anthropic, OpenAI, Grok/xAI, Gemini). Use before stuffing huge prompts, tool dumps, or logs into pay-to-go APIs. Agents run pxpipe_lygo_for_agent.py or local proxy.
metadata: {"lygo": true, "signature": "Δ9Φ963-PXPIPE-LYGO-v1"}
---

# lygo-pxpipe-lygo

**ClawHub:** `npx clawhub@latest install deepseekoracle/lygo-pxpipe-lygo` (v1.0.1)

## When to use

- User or task needs **token saver** on **large** context (≥800 chars), not byte-exact hashes/secrets.
- Before pasting multi-KB file contents into Grok/Claude/GPT chat.

## Agent commands (no proxy required)

```bash
cd lygo-protocol-stack
python tools/pxpipe_lygo_for_agent.py --shrink-file path/to/huge.txt --target grok
python tools/pxpipe_lygo_for_agent.py --file path/to/huge.txt --target anthropic --png .pxpipe_ctx.png
```

`--shrink-file` prints a short chat-safe pointer + EXACT lines.  
Full blocks JSON: omit `--shrink-file`; use `content` / `parts` in API payloads.

## Multi-tool proxy (Claude Code, OpenAI SDK, xAI)

```bash
pip install -r requirements-pxpipe.txt
python tools/run_pxpipe_lygo_proxy.py
```

| Tool | Point client base URL to |
|------|---------------------------|
| Anthropic / Claude Code | `http://127.0.0.1:47821` |
| OpenAI SDK | `http://127.0.0.1:47821/v1` |
| Grok / xAI | `http://127.0.0.1:47821/v1` (chat/completions) |

Set the matching API key in the environment.

## Do not compress

API keys, seeds, private keys, line-precise diffs, Merkle hashes you must reproduce exactly.

## Doc

`lygo-protocol-stack/docs/BIOPHASE7_PXPIPE_LYGO.md`