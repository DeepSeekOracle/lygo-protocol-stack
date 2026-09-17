# Biophase7 → pxpipe-LYGO (lattice module)

**Provenance:** `LYRA SYSTEM RETORE/FINAL RESTORE/ALL SEALS/220+/New folder/2026Biophase7/Crete a LYGO version - ✅ What pxpip.txt`  
**Upstream inspiration:** [teamchong/pxpipe](https://github.com/teamchong/pxpipe) (text context → PNG for vision APIs).  
**Canonical implementation:** `lygo-protocol-stack/pxpipe_lygo/`

## What LYGO adds over pxpipe

| pxpipe | pxpipe-LYGO |
|--------|-------------|
| Anthropic-focused proxy | P0 profitability gate + local manifests |
| No audit trail | `data/pxpipe_lygo/manifests/` + optional P1 scatter |
| No lattice hooks | P3 vortex signature on manifest JSON |
| Lossy vision for everything | Verbatim guard (hashes, keys, long IDs stay as text) |

P0 is **not** content moderation — see [`P0_HONEST_SPEC.md`](P0_HONEST_SPEC.md).

## Quick start

```bash
cd lygo-protocol-stack
pip install Pillow
python -m pxpipe_lygo.cli compress --file path/to/large_prompt.txt
python tools/run_pxpipe_lygo_proxy.py
```

### Agents (Grok Build, scripts, other tools)

No proxy needed — emit provider-ready JSON blocks:

```bash
python tools/pxpipe_lygo_for_agent.py --file big_context.txt --target grok --png .pxpipe_ctx.png
python tools/pxpipe_lygo_for_agent.py --shrink-file big_context.txt --target auto
```

`--shrink-file` returns a short chat pointer + EXACT identifiers for the main thread.

### Multi-tool proxy (`127.0.0.1:47821`)

| Endpoint | Clients |
|----------|---------|
| `POST /v1/transform` | `{"text":"...","target":"anthropic\|openai\|grok\|gemini"}` |
| `POST /v1/compress` | Raw compressor + optional `include_blocks` |
| `POST /v1/messages` | Anthropic API (compress + forward) |
| `POST /v1/chat/completions` | OpenAI + xAI Grok (`?provider=grok` or `openai`) |

| Tool | Base URL env |
|------|----------------|
| Claude / Claude Code | `ANTHROPIC_BASE_URL=http://127.0.0.1:47821` |
| OpenAI SDK | `OPENAI_BASE_URL=http://127.0.0.1:47821/v1` |
| xAI / Grok | `XAI_BASE_URL=http://127.0.0.1:47821/v1` |

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `LYGO_PXPIPE_MIN_CHARS` | 800 | Minimum text size to consider |
| `LYGO_PXPIPE_MIN_SAVINGS` | 1.35 | Text tokens must exceed vision estimate × ratio |
| `LYGO_PXPIPE_PORT` | 47821 | Proxy port |
| `LYGO_PXPIPE_USE_P1` | 1 | Store manifest bytes in P1 mycelium |
| `LYGO_PXPIPE_ANCHOR` | 0 | Run `lygo_anchor.py` on each manifest (consent/offline) |

## Lattice

Verified by `tools/verify_lattice_alignment.py` (pxpipe module + doc + tests).

Do **not** use PNG compression for byte-exact code diffs, seeds, or private keys — use verbatim guard output only as hints; keep secrets out of prompts.