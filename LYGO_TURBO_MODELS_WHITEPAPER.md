# LYGO Turbo Models — Flagship Local AI Starting Lineup

**Signature:** `Delta9Phi963-LYGO-TURBO-MODELS-WHITEPAPER-v1.0`  
**Date:** 2026-07-21  
**Steward:** Justin Helmer (Lightfather) · Excavationpro · DeepSeekOracle  
**HTML page:** https://eternalhaven.ca/lygo-turbo-models-whitepaper.html  

## Abstract

First-generation **LYGO Turbo** local Ollama models for agents, coding, and tasking — specialized by **context budget**, **system contract**, and **role**. Built for stability on steward hardware (RTX 4060 Ti 8GB + 32GB RAM) and for LYGO infrastructure (Instructions Vault, Hermes, OpenClaw, USB CLAW, music lattice).

## Starting lineup

| Model | Base | num_ctx | Role |
|-------|------|---------|------|
| **lygo-turbo-coder** | qwen3-coder:30b Q4_K_M | **131072** | Flagship coding / scripts / encode / CLAW tasks |
| **lygo-turbo-hermes** | Uncensored 35B-A3B lineage | **65536** | Hermes multi-skill tools |
| **lygo-turbo-uncensored** | Uncensored lineage | **8192** | Portal / fast chat; optional :8000 API |
| **lygo-turbo-agent** | Uncensored lineage | **32768** | Optional mid agent |

### Why coder is qwen3-coder (not Nemotron Super)

- Nemotron Super ~86GB / 123B thrash risk on 32GB RAM
- Not code-specialized the way Qwen3-Coder is
- qwen3-coder:30b already local, tools-capable, native ctx to 262144

### Create coder

```bat
set OLLAMA_MODELS=D:\Ollama\.ollama\models
ollama create lygo-turbo-coder -f D:\Ollama\modelfiles\LYGO_TURBO_CODER.Modelfile
ollama run lygo-turbo-coder
```

## Design principles

1. Specialize with Modelfiles; do not thrash base blobs  
2. Context is a feature and a cost  
3. Procedure vault over freestyle shell  
4. Staging before production (music)  
5. Dual homes: OpenClaw D:\OpenClaw, models on D:, law on USB  

## Instructions Vault

- E:\LYGO_BUILDER_KEY\LYGO_INSTRUCTIONS_VAULT  
- D:\LYGO_INSTRUCTIONS_VAULT  
- Entry: 00_START\00_START_HERE.txt  

## Field lessons (2026-07-21)

- Hermes aligns and plans well at 65k  
- Freestyle ffmpeg fails; vault recipe/script succeeds  
- Custom domains need absolute lattice URLs  
- One large model load at a time on 8GB  

## Do not break

lygo-turbo-uncensored · lygo-turbo-hermes · lygo-turbo-coder · Instructions Vault dual paths  

## Related

- Session log: E:\LYGO_BUILDER_KEY\docs\LATTICE_SESSION_LOG_2026-07-21.txt  
- Modelfile: D:\Ollama\modelfiles\LYGO_TURBO_CODER.Modelfile  
- Immutable anchors: agents group entry lygo_turbo_models_whitepaper  

Delta9Phi963 — starting lineup for a sovereign lattice.
