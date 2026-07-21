# LYGO dual Ollama home (C + D)

**Problem:** OpenClaw / factory tools default to `C:\Users\<you>\.ollama` while large weights live under `D:\Ollama\.ollama\models`.

**Fix (already applied):**

| Layer | Setting |
|-------|---------|
| **Weights (canonical)** | `D:\Ollama\.ollama\models` (~185 GB) |
| **Factory home** | `C:\Users\justi\.ollama` (config, keys, doctor paths) |
| **Junction** | `C:\Users\justi\.ollama\models` → `D:\Ollama\.ollama\models` |
| **User env** | `OLLAMA_MODELS=D:\Ollama\.ollama\models` |
| **API** | `OLLAMA_HOST=127.0.0.1:11434` |
| **Binary** | `D:\Ollama\ollama.exe` / `ollama app.exe` |

So:

- Paths that open **`%USERPROFILE%\.ollama\models`** see the **same files as D:**  
- New `ollama pull` / doctor / OpenClaw factory go to **D:** via env + junction  
- Either path works:

```text
D:\Ollama\.ollama\models\...
C:\Users\justi\.ollama\models\...   (same content)
```

## Re-apply after Windows/Ollama update

```bat
D:\Ollama\LYGO_OLLAMA_BOOT.bat
```

or:

```powershell
powershell -ExecutionPolicy Bypass -File D:\Ollama\scripts\ensure_dual_home.ps1
```

## OpenClaw

`C:\Users\justi\.openclaw\openclaw.json` uses:

```json
"baseUrl": "http://127.0.0.1:11434"
```

That is correct for **both** homes (one daemon). Restart **OpenClaw Gateway** after env change.

## Optional: prefer uncensored primary

Edit openclaw.json:

```json
"primary": "ollama/AI-TAVS/Qwen3.6-35b-a3b-Uncensored:35b"
```

## High-perf stack

`D:\LYGO_HIGHPERF` still hardlinks the uncensored blob from D models — unchanged.

## Do not

- Delete `D:\Ollama\.ollama\models` (canonical weights)
- Point `OLLAMA_MODELS` back to a empty C folder without the junction

**Δ9Φ963 — one library · two paths · one API :11434**
