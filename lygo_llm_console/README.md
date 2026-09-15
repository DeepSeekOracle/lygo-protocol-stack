# LYGO LLM Console

Sovereign local LLM runtime + agent portal. **Does not call `ollama.exe`.**

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
