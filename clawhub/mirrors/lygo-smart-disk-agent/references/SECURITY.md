# SECURITY — lygo-smart-disk-agent

**Signature:** `Δ9Φ963-SDA-SECURITY-v1.0.3`

## Trust model

| Assumption | Implication |
|------------|-------------|
| Portal binds **localhost** only | Same-machine operator is trusted |
| **No password** on local UI | Physical/local host access = operator (USB one-shot **by design**) |
| Ollama via `http://localhost:11434` | Model traffic local |
| No cloud API keys in package | Offline core path |

## Agentic controls (1.0.3)

| Control | Detail |
|---------|--------|
| Memory over HTTP | **Blocked** (`/api/memory` + limb `memory` → 403) |
| Chat persistence | **Metadata only** (hash + lengths; no full transcripts) |
| open-url over HTTP | **Blocked** |
| Status over HTTP | Host `root` path redacted |
| Bind guard | Refuse `0.0.0.0` without `LYGO_SDA_ALLOW_LAN=1` |
| CORS | No wildcard |
| POST cap | 64 KiB |
| Self-check | Static imports only (no dynamic module load) |

## CLI-only (after local install)

```bash
python agent/smart_disk_agent.py limb memory
python agent/smart_disk_agent.py limb open-url http://localhost:9631/
```

## Hard rules for agents

1. Do not rebind to public interfaces without human consent + auth.
2. Do not commit secrets or model weights.
3. Do not auto-publish or social post without user request.
4. P0 QUARANTINE = stop.

## Human review note

This skill is a **disclosed local AI portal**. Static malware patterns: none.  
Remaining review is **policy**: no-login localhost UI. Chat history is **not** exported through the HTTP limb interface as of 1.0.3.

See `SKILLSPECTOR_AUDIT.md`.

**Δ9Φ963 — consent · localhost · no HTTP memory export.**
