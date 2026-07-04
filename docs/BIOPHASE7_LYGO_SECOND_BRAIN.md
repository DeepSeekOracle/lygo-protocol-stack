# Biophase7 → LYGO Second Brain

**Source:** `2026Biophase7/lygo-second-brain.zip` + `READ IE DriveLYRA SYSTEM RETOREFINA.txt`  
**Stack path:** `lygo_second_brain/`  
**CLI:** `python tools/lygo_second_brain.py`  
**Install:** `python tools/install_lygo_second_brain.py`  
**ClawHub:** `deepseekoracle/lygo-second-brain`

## Philosophy

Karpathy-style persistent LLM wiki, **sovereignized** for LYGO:

- Vault on disk (Obsidian optional)
- Ollama for extract / embed / synthesize
- Git commit per ingest/wiki = audit trail
- Multi-model agreement via `consensus.py`

Corrections from the Biophase7 readme (implemented):

- No byte-entropy as quality filter — size/corruption guard only
- No fake `ollama run "research my vault"` — retrieval via `embed_index` + `search`
- No mandatory Arweave per note — optional kernel eggs with consent
- Skip `/dream` v1 until embeddings stable

## Files

| Path | Role |
|------|------|
| `lygo_second_brain/scripts/*.py` | ingest, index, search, consensus, wiki |
| `lygo_second_brain/vault/` | default vault (`LYGO_VAULT_ROOT`) |
| `clawhub/mirrors/lygo-second-brain/` | agent skill |
| `.grok/skills/lygo-second-brain/` | local Grok skill (install script) |
| `2026Biophase7/lygo-second-brain-LYGO/` | Biophase7 mirror (install script) |

## Verify

```bash
python clawhub/mirrors/lygo-second-brain/scripts/self_check.py
python tools/lygo_second_brain.py index   # needs Ollama + notes
```