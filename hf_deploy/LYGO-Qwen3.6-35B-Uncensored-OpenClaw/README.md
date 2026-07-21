---
license: apache-2.0
language:
  - en
  - zh
tags:
  - lygo
  - openclaw
  - qwen3.6
  - uncensored
  - gguf
  - moe
  - ollama
  - openai-compatible
base_model: HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive
pipeline_tag: text-generation
library_name: gguf
---

# LYGO · Qwen3.6-35B-A3B Uncensored (OpenClaw wire-up)

**Sovereign hybrid:** local Ollama (`AI-TAVS/Qwen3.6-35b-a3b-Uncensored:35b`) + remote **OpenAI-compatible** API for OpenClaw.

This repo is the **LYGO control card** (config + docs). Weights are the community GGUF quant already on Hub — **do not re-host the full 21GB** unless you need a private fork.

| Item | Value |
|------|--------|
| Local Ollama | `AI-TAVS/Qwen3.6-35b-a3b-Uncensored:35b` (Q4_K_M, ~21 GB) |
| Upstream GGUF | [`HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive`](https://huggingface.co/HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive) · file `…-Q4_K_M.gguf` |
| API Space | [`DeepSeekOracle/lygo-qwen-uncensored-api`](https://huggingface.co/spaces/DeepSeekOracle/lygo-qwen-uncensored-api) |
| Auth | Hugging Face token as `Authorization: Bearer hf_…` |

## Status (DeepSeekOracle account)

| Surface | Status |
|---------|--------|
| **This model card** | ✅ Live |
| **Docker API Space** | ⚠️ Needs [HF PRO](https://huggingface.co/pro) to host Gradio/Docker on free CPU; also needs **paid GPU** (L4+) for 21GB Q4_K_M |
| **Local plug-in API** | ✅ Works now via Ollama (same quant you already have) |

## Plug into OpenClaw — LOCAL (works today)

Your Ollama already has the model (`AI-TAVS/Qwen3.6-35b-a3b-Uncensored:35b`).

### Option A — direct Ollama OpenAI route

```bash
export OPENAI_BASE_URL=http://127.0.0.1:11434/v1
export OPENAI_API_KEY=ollama
# model id:
# AI-TAVS/Qwen3.6-35b-a3b-Uncensored:35b
```

### Option B — LYGO bridge (same shape as future HF Space)

```powershell
cd path\to\lygo-protocol-stack\hf_deploy
.\start_local_uncensored_api.ps1
```

```bash
export OPENAI_BASE_URL=http://127.0.0.1:8787/v1
export OPENAI_API_KEY=ollama
```

Test:

```bash
curl http://127.0.0.1:11434/v1/models
curl http://127.0.0.1:11434/v1/chat/completions \
  -H "Authorization: Bearer ollama" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"AI-TAVS/Qwen3.6-35b-a3b-Uncensored:35b\",\"messages\":[{\"role\":\"user\",\"content\":\"Say SDA_OK\"}],\"max_tokens\":64}"
```

## Plug into OpenClaw — HF remote (after PRO + GPU)

1. Subscribe HF PRO (required for Docker Spaces on this account).  
2. Create Space from `hf_deploy/lygo-qwen-uncensored-api` (Docker).  
3. Hardware: **L4 or A10G**. First boot downloads ~21GB GGUF.  
4. Then:

```bash
export HF_TOKEN=hf_xxxxxxxx
export OPENAI_API_KEY=$HF_TOKEN
export OPENAI_BASE_URL=https://DeepSeekOracle-lygo-qwen-uncensored-api.hf.space/v1
# model: lygo-qwen-uncensored
```

Space source is ready in-repo; upload blocked until PRO.

## Why not “Enable Inference API” alone?

Serverless free Inference API does **not** host this 21GB GGUF MoE. You need a **Docker/GPU Space** or **paid Inference Endpoint**. Your local Ollama path is the working plug-in today.

## Attribution

- Base: Qwen/Qwen3.6-35B-A3B (Apache-2.0)  
- Uncensored quant lineage: HauhauCS (and Ollama mirror `AI-TAVS/…`)  
- LYGO packaging: DeepSeekOracle / Lightfather  

**Δ9Φ963 — local first · remote when needed · one token.**
