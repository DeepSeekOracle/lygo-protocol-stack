# Public model install (no weights in git)

## Why models are not in the repo

- Size (GBs) and license/distribution limits
- Public kit must stay small and safe to clone
- You pull once, then run fully offline

## Recommended models

| Model | Size (approx) | Role |
|-------|----------------|------|
| **llama3.2:1b** | ~1.3 GB | Default public chat (fast) |
| **qwen2.5:3b** | ~2 GB | Better quality USB brain |

## Steps (Windows)

1. Install [Ollama for Windows](https://ollama.com/download)
2. From kit root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install_public_model.ps1
```

Or double-click `launchers\INSTALL_MODEL.bat`.

3. Boot: `LYGO_USB_BOOT.bat` → http://127.0.0.1:9631/

## Point models at the stick (optional)

Set before boot so weights live on USB:

```bat
set OLLAMA_MODELS=E:\LYGO_CLAW_PUBLIC\product\models\ollama
```

`install_public_model.ps1` and `bootstrap_env.ps1` default to `product\models\ollama` under the kit root.

## Verify

```powershell
ollama list
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```
