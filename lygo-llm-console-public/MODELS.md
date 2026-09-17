# Generic boot model (legal to redistribute as a download instruction)

The SkillHub FULL zip is the **console only**. Weights are **not** inside the zip (too large; license stays with the model author).

## One generic GGUF we point to (Apache-2.0)

**Qwen2.5-1.5B-Instruct Q4_K_M** from the official Qwen org.

| | |
|--|--|
| File | `qwen2.5-1.5b-instruct-q4_k_m.gguf` |
| Size | ~1.04 GB |
| License | Apache License 2.0 (see the model card) |
| SHA-256 | `6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e` |
| Download | https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf |
| Card | https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF |

Verify:

```
certutil -hashfile qwen2.5-1.5b-instruct-q4_k_m.gguf SHA256
```

Put the file in the console `models\` folder (create it). Boot `LYGO_LLM_CONSOLE.bat`, click **Scan drives**, select the Qwen 1.5B tag, **Boot LLM**.

This is enough for a KERNEL-level local agent loop (tools, search, SOUL/MEMORY). It is small; add larger GGUFs later if you have RAM.

## Add more models (your downloads)

Drop any `*.gguf` into `models\` or keep Ollama blobs under `%USERPROFILE%\.ollama\models`. Scan again. You are responsible for each model's license (Llama, Gemma, etc.).

## Engine (not a model)

`engine\llama-server.exe` from ggml-org llama.cpp **b10988** Windows CPU zip. Not Ollama's nested copy.

We do **not** ship Meta Llama weights with this pack.
