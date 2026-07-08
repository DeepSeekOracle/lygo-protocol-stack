# LYGO Second Brain (Biophase7)

Local-first **LLM wiki** for the LYGO lattice: Obsidian-compatible markdown vault + Ollama scripts. Honest scope — no cloud API requirement, no blockchain anchoring (git commits are the audit trail).

**Provenance:** `2026Biophase7/lygo-second-brain.zip` + `READ IE DriveLYRA SYSTEM RETOREFINA.txt`

## LYGO mapping (honest)

| Karpathy / myth name | LYGO delivery |
|----------------------|---------------|
| Claude + Obsidian | Ollama + this vault (`LYGO_VAULT_ROOT`) |
| Cloud deep research | `consensus.py` + vault retrieval |
| P0 entropy filter | Size/corruption check in `ingest.py` |
| P1 mycelium | `manifest.jsonl` + git history |
| P3 vortex consensus | `consensus.py` (multi-model cosine agreement) |
| Kernel Eggs / Arweave | **Optional** `lygo-kernel-egg-planter` — not required for v1 |

## Quick start

```powershell
cd I:\E Drive\lygo-protocol-stack
python tools/install_lygo_second_brain.py
$env:LYGO_VAULT_ROOT = "I:\E Drive\lygo-protocol-stack\lygo_second_brain\vault"
ollama pull llama3.2
ollama pull nomic-embed-text
cd lygo_second_brain\scripts
python ingest.py ..\vault\raw\your-note.txt --vault ..\vault
python embed_index.py --vault ..\vault
python search.py "LYGO sovereign stack" --vault ..\vault
```

Or use the stack CLI:

```bash
python tools/lygo_second_brain.py ingest raw/example.md
python tools/lygo_second_brain.py index
python tools/lygo_second_brain.py wiki "second brain"
```

## Vault layout

- `vault/raw/` — drop sources
- `vault/permanent/` — atomic notes
- `vault/wiki/` — synthesized topic pages
- `vault/archive/` — ingested originals
- `vault/.vault_index.sqlite3` — local embeddings (gitignored)

## Agent / security

ClawHub skill: `lygo-second-brain`. Read `references/SECURITY.md` — no auto git push, no secrets in vault, consent before planting kernel eggs.