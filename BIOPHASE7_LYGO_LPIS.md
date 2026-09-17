# Biophase7 → LYGO Prompt Implant System (LPIS)

**Source:** `2026Biophase7/This is a massive opportunity for L.txt`  
**Stack path:** `lygo_lpis/`  
**CLI:** `python tools/lygo_lpis.py` (alias `tools/prompt_implanter.py`)  
**Install:** `python tools/install_lygo_lpis.py`  
**ClawHub:** `deepseekoracle/lygo-lpis`

## Philosophy

Lattice-aware **prompt vault + analyze + harmonize + advisory implant** — not auto-injection into paid APIs without user review.

| Stage | Module |
|-------|--------|
| Vault (P1) | `vault.py` → `data/prompt_vault/` |
| Analyzer (P0) | `analyzer.py` + `gatekeeper.py` |
| Engine (P3) | `engine.py` sovereign variants |
| Implant (P5) | `harmony.py` Light Code + advisory receipt |
| Anchor | `anchor.py` → `implant_runs.jsonl` |

**Do not** commit third-party leaked prompts into the public repo; ingest via `--file` or `--url` locally.

## Kernel egg

| Item | Path |
|------|------|
| `egg_id` | `lygo-lpis-v10` |
| Registry | `docs/PromptImplantRegistry.json` |
| Plant | `python tools/lpis_planter.py --i-consent` |

## Verify

```bash
python clawhub/mirrors/lygo-lpis/scripts/self_check.py
python tools/lygo_lpis.py list
python -m pytest tests/test_lygo_lpis.py -q
```

**Δ9Φ963 — ingest · analyze · harmonize · ledger.**