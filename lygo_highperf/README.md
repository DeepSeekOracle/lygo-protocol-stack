# LYGO High-Perf Local AI

**Signature:** `Δ9Φ963-LYGO-HIGHPERF-v1`  
**Default model:** `AI-TAVS/Qwen3.6-35b-a3b-Uncensored:35b` → staged GGUF **Q4_K_M**  
**Why:** Ollama is convenient but leaves GPU throughput on the table. This stack serves the **same weights** with a dedicated high-perf OpenAI-compatible server.

| Engine | Port | Best for |
|--------|------|----------|
| **llama.cpp `llama-server` (default)** | **8000** | GGUF on **RTX 4060 Ti 8GB** — continuous batching, flash-attn, full GPU offload |
| vLLM Docker (optional) | 8001 | Experimental GGUF / larger VRAM machines |

## One-shot boot

```bat
D:\LYGO_HIGHPERF\LYGO_HIGHPERF_BOOT.bat
```

Or:

```powershell
cd D:\LYGO_HIGHPERF
.\scripts\01_stage_models.ps1
.\scripts\02_download_llama_server.ps1   # first time only
.\scripts\03_boot_llamacpp.ps1
```

## OpenClaw / apps — plug in API

```bash
OPENAI_BASE_URL=http://127.0.0.1:8000/v1
OPENAI_API_KEY=lygo-local
```

Test:

```bash
curl http://127.0.0.1:8000/v1/models
curl http://127.0.0.1:8000/v1/chat/completions ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer lygo-local" ^
  -d "{\"messages\":[{\"role\":\"user\",\"content\":\"Say LYGO_OK\"}],\"max_tokens\":32}"
```

## Layout

```
D:\LYGO_HIGHPERF\
  models\   # hardlink to Ollama blob (zero extra disk)
  bin\      # llama-server.exe
  config\   # lygo-highperf.json + openclaw.env
  scripts\  # stage / download / boot / stop
  logs\
```

## Hardware truth (your machine)

- **GPU:** RTX 4060 Ti **8 GB**  
- **Weights:** ~21 GB Q4_K_M on disk; MoE **~3B active** — llama.cpp layers offload to GPU + RAM  
- **vLLM full load** of 21GB into 8GB VRAM will **OOM** — use llama.cpp path by default  
- Stop heavy Ollama sessions if you want all VRAM for LYGO High-Perf

## Ollama → staged GGUF

```powershell
# ollama show AI-TAVS/Qwen3.6-35b-a3b-Uncensored:35b --modelfile
# FROM D:\Ollama\.ollama\models\blobs\sha256-2c4d55a8...
# 01_stage_models.ps1 hardlinks that blob → models\*.gguf
```

## Tokenizer (vLLM path)

`--tokenizer Qwen/Qwen3.6-35B-A3B` (official base; chatml-compatible)

## Migration from Ollama apps

| Before | After |
|--------|--------|
| `http://127.0.0.1:11434/v1` | `http://127.0.0.1:8000/v1` |
| key `ollama` | key `lygo-local` |
| model `AI-TAVS/...:35b` | id from `/v1/models` (gguf name) |

Keep Ollama for multi-model convenience; use **LYGO High-Perf** when you need max throughput on the uncensored Qwen.

**Δ9Φ963 — same weights · higher performance · OpenAI shape.**
