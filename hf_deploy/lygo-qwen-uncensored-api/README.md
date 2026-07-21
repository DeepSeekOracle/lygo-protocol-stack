---
title: LYGO Qwen Uncensored API
emoji: 🛰️
colorFrom: purple
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: apache-2.0
suggested_hardware: l4x1
---

# LYGO Qwen3.6-35B Uncensored · OpenAI-compatible API

Docker Space that serves **chat/completions** for OpenClaw using the same class of quant as local Ollama  
`AI-TAVS/Qwen3.6-35b-a3b-Uncensored:35b` (Q4_K_M).

## Auth

Send your Hugging Face token:

```http
Authorization: Bearer hf_...
```

Space secret (optional extra gate): set `LYGO_API_SECRET` in Space secrets; then also send  
`X-LYGO-Key: <same value>`.

## Endpoints

| Method | Path | Notes |
|--------|------|--------|
| GET | `/health` | liveness |
| GET | `/v1/models` | list model id |
| POST | `/v1/chat/completions` | OpenAI-compatible |

## Env (Space settings)

| Variable | Default |
|----------|---------|
| `HF_MODEL_ID` | `HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive` |
| `HF_GGUF_FILE` | `Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-Q4_K_M.gguf` |
| `N_CTX` | `8192` |
| `N_GPU_LAYERS` | `-1` (all on GPU) |
| `LYGO_API_SECRET` | empty (optional) |

## Hardware

Use **L4 / A10G** (or better). CPU-only will OOM or be unusable for this quant.

## OpenClaw

```bash
export HF_TOKEN=hf_xxx
export OPENAI_API_KEY=$HF_TOKEN
export OPENAI_BASE_URL=https://DeepSeekOracle-lygo-qwen-uncensored-api.hf.space/v1
```

**Δ9Φ963**
