# LYGO LLM Console (admin / steward tree)

Sovereign local LLM runtime + agent portal. **Does not call `ollama.exe`.**

**Channel:** ADMIN. Not the ClawHub tentacle. Public kit + page: https://chatagent.ca/lygo-llm-console.html  
Public zip: `lygo-llm-console-public.zip`. Do not publish this admin tree’s extra roots or keys.

Signature: `Δ9Φ963-LYGO-LLM-CONSOLE-v1`

Whitepaper: [`docs/whitepapers/LYGO_LLM_CONSOLE_v1.md`](../docs/whitepapers/LYGO_LLM_CONSOLE_v1.md)

## Boot (Windows)

Double-click `LYGO_LLM_CONSOLE.bat` or:

```bat
python -u src\server.py serve
```

Portal: http://127.0.0.1:9641/  
Private llama-server: `127.0.0.1:11441` (internal `--api-key`)

Python discovery: `%LYGO_PYTHON%` → `U:\LYGO\projects\python\python.exe` → `C:\Python313\python.exe` → `py`

No Ollama probe. No npm. No pip.

## Tests

```bat
python -m unittest discover -s tests -v
```

## Engine

Put ggml-org `llama-server.exe` (CPU zip) in `engine/`. See `engine/README.md`.  
Refuse nested `projects\ollama\lib\ollama`.

## Doctrine

Dual ledgers / Star Chart remain CANON. Grokipedia is RESOURCE. Hub never replace/delete CANON.

Donate: [PayPal.me/ExcavationPro](https://paypal.me/ExcavationPro) · arcade https://chatagent.ca/games/


## Public kit

This zip is the **public** channel. It is not the steward admin tree. Write roots stay inside this folder. Place ggml-org `llama-server.exe` in `engine/` (CPU Windows zip). Page: https://chatagent.ca/lygo-llm-console.html
