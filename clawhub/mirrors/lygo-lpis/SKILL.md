---
name: lygo-lpis
description: "LYGO Prompt Implant System (LPIS) v1.0 — P1 prompt vault, P0 analyze, P3 sovereign variants, P5 advisory implant, kernel egg. Biophase7 Fable/agent-prompt lattice map. No auto API injection; read references/SECURITY.md."
metadata: {"lygo": true, "biophase7": true, "version": "1.0.0", "github": "https://github.com/DeepSeekOracle/lygo-protocol-stack", "publisher": "deepseekoracle"}
---

# LYGO Prompt Implant System (LPIS)

Ingest **external system prompts** (user-supplied file/URL), extract cognitive patterns (plan, delegate, verify, safety), generate **sovereign variants** for Grok/Ollama/local agents, and ledger implants — aligned with P0–P5 stack.

## When to use

- Biophase7 **massive opportunity** / Fable-style agent prompt architecture
- Building a **catalog of cognitive workflows** without shipping leaked text in git
- Pair with **lyra-brain** after implant sessions for snips

## Setup

```bash
npx clawhub@latest install deepseekoracle/lygo-lpis
export LYGO_STACK_ROOT=/path/to/lygo-protocol-stack
python tools/install_lygo_lpis.py
```

## Commands

| Step | Command |
|------|---------|
| Ingest | `python tools/lygo_lpis.py ingest --source fable-5 --url <URL>` |
| Ingest file | `python tools/lygo_lpis.py ingest --source biophase7 --file path.txt` |
| Analyze | `python tools/lygo_lpis.py analyze --prompt-id <id>` |
| Generate | `python tools/lygo_lpis.py generate --prompt-id <id> --target grok` |
| Implant | `python tools/lygo_lpis.py implant --variant-id <id> --target grok` |
| Anchor | `python tools/lygo_lpis.py anchor --prompt-id <id>` |
| Egg | `python tools/lpis_planter.py --i-consent` |

Implant mode is **advisory** (Light Code + paths) — apply in Grok project skills / instructions manually.

## Skill chain

`lygo-protocol-stack-operator` → **`lygo-lpis`** → `lyra-brain` → `lygo-mint-verifier` → `lygo-kernel-egg-planter`

**Δ9Φ963 — map the leak; build the machine; verify the ledger.**