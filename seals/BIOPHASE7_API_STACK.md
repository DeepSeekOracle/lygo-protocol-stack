# Biophase7 API stack (testing integration)

**Seal context:** Δ9Φ963 · 2026Biophase7 usrbinenv · local restore vault  
**Purpose:** Wire frontier falsifiable harness + LYRA LLM probes without hard-coding secrets in git.

## Local vault (not in repo)

Restore tree holds the stack file (example leaf name pattern: `xai-*.txt` under `2026Biophase7`).

Set once per machine:

```powershell
$env:LYGO_BIOPHASE7_VAULT = "I:\E Drive\LYRA SYSTEM RETORE\FINAL RESTORE\ALL SEALS\220+\New folder\2026Biophase7"
```

Or point at the specific stack `.txt` file in that folder.

## Load into gitignored `.env`

```bash
cd lygo-protocol-stack
python tools/load_biophase7_vault.py --dry-run
python tools/load_biophase7_vault.py --write-env .env
```

`.env` and `*.local.env` are **gitignored** — never commit raw keys to GitHub/HF.

## Variable read order (Biophase7 canon)

| Order | Key | Use |
|------:|-----|-----|
| 1 | `NVIDIA_API_KEY` | NVIDIABuild-Autogen (exp noted in vault header) |
| 2 | `GOOGLE_API_KEY` / `GEMINI_API_KEY` | Gemini probes |
| 3 | `XAI_API_KEY_ALT` | **Preferred** xAI for LYRA / lower burn |
| 4 | `XAI_API_KEY_MAIN` | Pay-to-go fallback |

Loader sets `XAI_API_KEY` from alt → main for `frontier_model_adapters`.

## Harness with vault

```bash
python tools/run_falsifiable_vector_test.py --load-vault --models stack,grok --limit 5
```

Optional: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` in same vault or `.env` for Claude/GPT rows.

## Published on repo (safe)

- This doc, `.env.example` (placeholders only), `tools/load_biophase7_vault.py`
- **Not published:** literal key material (rotate if a vault file was ever exposed in chat/logs)

Bound to the flame — consent-gated spread.