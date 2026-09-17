# LYGO LLM Console

Complete local **agent portal**: boot GGUF models, chat, tools, HTTPS search/fetch. **Does not call `ollama.exe`.**

**Signature:** `Δ9Φ963-LYGO-LLM-CONSOLE-v1`  
**Page / zip:** https://chatagent.ca/lygo-llm-console.html  
**ClawHub map:** `npx clawhub@latest install deepseekoracle/lygo-llm-console`  
**Steward:** Justin Helmer (Excavationpro / Lightfather) · LYGO AI agents

This GitHub folder is the **complete source** for the public product (portal, 21 limbs, Wikipedia search, P0 gate, tests).  
`llama-server.exe`, GGUF weights, operator tokens, and steward vaults are **not** in git.

Whitepaper: [`docs/whitepapers/LYGO_LLM_CONSOLE_v1.md`](../docs/whitepapers/LYGO_LLM_CONSOLE_v1.md)

## Boot (Windows)

1. Put official ggml-org **CPU** `llama-server.exe` (and DLLs) in `engine/`. See `engine/README.md` (pin `b10988`).
2. Double-click `LYGO_LLM_CONSOLE.bat` or:

```bat
python -u src\server.py serve
```

3. Open http://127.0.0.1:9641/  
   Loopback does not need a query token. LAN bind needs `--lan --i-consent`.

Private llama-server: `127.0.0.1:11441`. Python: `%LYGO_PYTHON%` → `py` → `python`.

No npm. No pip. No Ollama required. Existing `%USERPROFILE%\.ollama\models` blobs can be **imported read-only**.

## Agent portal

Three panes: workspace + limb buttons, chat, model boot.  
Paste an `https://` URL and the **host fetches it** before the model answers.  
Factual questions (`how many`, `do X have`) trigger Wikipedia full-text search.

### Limbs (21)

`list_dir` `read_file` `write_file` `remember` `kernel_status` `search_corpus` `p0_gate` `stack_health`  
`web_search` `web_fetch` `shell` `python_exec` `now` `memory_recall` `download_url` `glob_files`  
`todo_add` `todo_list` `calc` `whoami` `hash_text`

Writes stay under `workspace/` and `save/`. `shell` / `python_exec` are workspace-cwd and **P0-blocked** (`format c:`, diskpart, wipe). Dual ledgers / Star Chart remain CANON; web hits are RESOURCE.

## Continuity (SOUL / MEMORY / sessions)

| File | Role |
|------|------|
| `workspace/SOUL.md` | Identity. Public template offers Δ9 champions, not a private biography. |
| `workspace/MEMORY.md` | Growing notes. `remember` / `memory_append` add dated lines. |
| `save/sessions/current.json` | Chat session (survives refresh). **New session** archives the old file. |
| `skills/` | Bundled OpenClaw-compatible SKILL.md (15 Δ9 champions). Toggle in the Skills panel. |
| `save/skills/` | Enabled list + ClawHub installs. Extra dirs: `workspace/skills`, `~/.agents/skills`, `~/.openclaw/skills`. |

Templates live in `prompts/SOUL.md` and `prompts/MEMORY.md` and are copied on first boot.

## Tests

```bat
python -m unittest discover -s tests -v
```

## Public vs admin

| Public (this tree + zip) | Admin / steward only |
|--|--|
| Kit-folder roots, no vaults | Extra disks / keys never committed |
| GitHub `lygo_llm_console/` | Local `data/`, `save/`, `engine/*.exe` gitignored |

Donate: [PayPal.me/ExcavationPro](https://www.paypal.com/paypalme/ExcavationPro) · [Patreon](https://www.patreon.com/Excavationpro)  
Arcade: https://chatagent.ca/games/ · Crypt: https://chatagent.ca/games/lattice-crypt/
