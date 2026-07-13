---
name: lygo-api-token-saver
description: Minimize pay-to-go xAI/API token spend. Use when user says token saver, save tokens, API budget, pay-to-go burn, or before long Grok/Claude/GPT calls. Prefer local Ollama army; Biophase7 alt xAI key; compact agent behavior.
metadata: {"lygo": true, "budget": true, "ollama": true, "signature": "Δ9Φ963-TOKEN-SAVER-v2", "version": "1.1.0"}
---

# LYGO API token saver

## Token Saver Hub (integrated router)

Routes mundane work to **local Ollama** (zero API tokens). Wired to slim army + pxpipe + savings journal.

```powershell
# Status (Ollama, vault mode, journal totals, lattice)
python "I:\E Drive\.grok\skills\lygo-api-token-saver\scripts\token_saver_hub.py" --status

# Summarize / draft / classify locally (sync, default)
python scripts/token_saver_hub.py --route summarize --file big_log.txt
python scripts/token_saver_hub.py --route draft --text "reply to user about lattice status"
python scripts/token_saver_hub.py --route explore --file repo_notes.md

# Force army queue path (hb-light / stack-worker picks up)
python scripts/token_saver_hub.py --route classify --file huge.txt --queue
```

**Journal:** `lygo-ollama-army/ollama_command_center/workspace/token_saver_journal.jsonl`  
**Config:** `army_config.json` → `token_saver` block (`compress_threshold_chars`, `prefer_queue`, model).

Auto-shrink: text over 6k chars → pxpipe shrink (if stack installed) or safe truncate before local LLM.

## API key order (Biophase7)

1. **Never** paste keys in chat or commits.
2. Load vault: `python tools/load_biophase7_vault.py` → uses `XAI_API_KEY_ALT` before `XAI_API_KEY_MAIN`.
3. Frontier harness / probes: default `--models stack` only; add `grok` only when user explicitly needs frontier rows.
4. Set `LYGO_OPENAI_FRONTIER_MODEL` only when OpenAI runs are required.

## pxpipe-LYGO (vision context compression)

When prompts/tool dumps are huge and byte-exact hashes are not the focus:

```bash
cd lygo-protocol-stack
pip install -r requirements-pxpipe.txt
python tools/run_pxpipe_lygo_proxy.py
```

See `docs/BIOPHASE7_PXPIPE_LYGO.md` and skill `lygo-pxpipe-lygo`. Agent one-liner:

`python tools/pxpipe_lygo_for_agent.py --shrink-file <huge.txt> --target grok`

Do **not** compress secrets, seeds, or diff-critical line numbers.

## Prefer local silicon (zero API tokens)

```powershell
# USB boot: Ollama + gateway + slim army (hb-light + stack-worker)
I:\E Drive\LYGO_BUILDER_KEY\LYGO_USB_Daemon_Supervisor.ps1 -DedupeDaemons

# Army health + token saver status
python ollama_command_center\scripts\army_health_check.py
python ..\lygo-api-token-saver\scripts\token_saver_once.py
```

| Task | Route locally | Escalate API only when |
|------|---------------|------------------------|
| Summarize logs/files | `--route summarize` | User needs frontier reasoning |
| Draft replies | `--route draft` | Brand/legal critical copy |
| Classify/triage | `--route classify` / `triage` | Ambiguous escalation |
| Repo explore/skim | `--route explore` + grep/limit reads | Architecture decisions |
| Lattice/stack ops | army `stack-worker` cron | Never auto — local only |

- LFW path: `lyra_failsafe()` → `LYGO_LFW_FALLBACK_MODEL` on Ollama when cloud throttled.

## Agent behavior (Grok Build)

| Do | Don't |
|----|--------|
| `token_saver_hub.py --status` before big tasks | Blind full-context API calls |
| Short replies; tables over prose | Re-summarize full session history |
| `grep` + `read_file` with `offset/limit` | `read_file` entire 3k-line trees |
| Hub `--route summarize` on large files | Paste 50k chars into chat |
| One subagent for execute batches | Many sequential full-context turns |
| `background: true` for HF push / long tests | Block chat on 10min uploads |
| Stop when task done | "Resonance forward" essays |

## Frontier harness (metered)

```bash
python tools/run_falsifiable_vector_test.py --load-vault --models stack
# API spend only if asked:
python tools/run_falsifiable_vector_test.py --load-vault --models grok --limit 3
```

Full 60× Grok ≈ high token + latency cost — require explicit user consent.

## User phrases → mode

- **"token saver" / "pay to go"** → hub local routes, slim army, alt xAI, minimal chat output.
- **"push all"** → one subagent; don't re-read diff in main thread.

## Self-check

```bash
python scripts/token_saver_hub.py --status
python -c "import os; print('alt' if os.environ.get('XAI_API_KEY_ALT') else 'no-vault')"
```

Install companions: `lygo-ollama-army`, `lygo-pxpipe-lygo`, `lygo-protocol-stack-operator`.