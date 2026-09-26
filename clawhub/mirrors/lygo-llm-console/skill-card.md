# lygo-llm-console (v1.6.0)

**One line:** a local, sovereign LLM runtime and agent portal you run yourself — scan GGUF, boot
llama.cpp on loopback, chat with tools, gate every turn through LYGO P0. Not Ollama.

**Ships:** map scripts + the public console kit, unpacked (console 1.5.6, 152 files, per-file SHA-256).

**Needs:** Python 3 on PATH, an unprivileged user account, and a ggml-org CPU `llama-server.exe`
(tag b11074) you place in `kit/engine/`. No model weights are included.

**Ask it for:** local chat, GGUF scanning, tool-using local agents, RAG over your own folder, an
OpenAI-shaped local endpoint other apps can point at.

**Do not ask it for:** cloud inference, a shared multi-user service, a hard sandbox, or LYGO CANON.

**Verify:** `python scripts/verify_kit.py` — if it fails, do not run the BAT.
