# OpenClaw + LYGO Qwen Uncensored API (HF)

## What you get

| Piece | URL / path |
|-------|------------|
| Model card | https://huggingface.co/DeepSeekOracle/LYGO-Qwen3.6-35B-Uncensored-OpenClaw |
| API Space | https://huggingface.co/spaces/DeepSeekOracle/lygo-qwen-uncensored-api |
| Local Ollama (same quant class) | `AI-TAVS/Qwen3.6-35b-a3b-Uncensored:35b` |
| Upstream GGUF | `HauhauCS/…-Q4_K_M.gguf` (~21 GB) |

## 1) Create HF token

https://huggingface.co/settings/tokens → **Write** (or Read if Space is public) → copy `hf_…`

## 2) Space hardware (required)

35B Q4_K_M needs GPU:

1. Open Space → **Settings → Hardware** → **Nvidia L4** (or A10G small)  
2. First boot downloads ~21 GB GGUF (slow once)  
3. Check `/health` until `model_loaded` or `gguf_present` is true  

Without GPU the Space will return 503.

## 3) Plug into OpenClaw

```bash
export HF_TOKEN=hf_xxxxxxxx
export OPENAI_API_KEY=$HF_TOKEN
export OPENAI_BASE_URL=https://DeepSeekOracle-lygo-qwen-uncensored-api.hf.space/v1
```

OpenClaw / gateway model id:

```text
lygo-qwen-uncensored
```

## 4) Local hybrid (home PC — no HF cost)

```bash
# terminal A
ollama serve
# model already present: AI-TAVS/Qwen3.6-35b-a3b-Uncensored:35b

# terminal B — OpenAI shape for OpenClaw
cd hf_deploy/lygo-qwen-uncensored-api
python -m app.local_ollama_bridge
# OPENAI_BASE_URL=http://127.0.0.1:8787/v1
# OPENAI_API_KEY=ollama
```

## 5) Test

```bash
curl -s https://DeepSeekOracle-lygo-qwen-uncensored-api.hf.space/health

curl -s https://DeepSeekOracle-lygo-qwen-uncensored-api.hf.space/v1/chat/completions \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"lygo-qwen-uncensored\",\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}],\"max_tokens\":32}"
```

## Why we did not re-upload 21GB

Your Ollama blob is already the HauhauCS **Q4_K_M** file (same byte size). The Space downloads that official Hub file. Faster, legal attribution clear, no duplicate storage on your account.

## Sovereignty map

```
OpenClaw ──► HF_TOKEN + Space API (remote, GPU)
         └─► local Ollama / bridge (sensitive, free, offline)
```

**Δ9Φ963 — one key · OpenAI shape · local when home.**
