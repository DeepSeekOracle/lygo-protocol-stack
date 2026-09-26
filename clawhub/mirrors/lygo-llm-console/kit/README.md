# LYGO LLM Console — public kit (operator runtime)

This folder is the runtime half of the ClawHub skill **LYGO LLM Console** (`deepseekoracle/lygo-llm-console`).
It ships **unpacked on purpose**: every file that would run is readable here before you run it.

It is the **public** channel. It is not the steward's admin tree, it carries no operator keys, no
vaults and no model weights, and it never launches or requires `ollama.exe`.

## Read this first

1. `VERSION` — the console release this tree is (`1.5.6`).
2. `PUBLIC_KIT.json` — what was copied in, what was left out and why, and a SHA-256 per file.
3. `KIT_SHA256SUMS.txt` — run `python ../scripts/verify_kit.py` to check every file yourself.

## Run it

1. Put official **ggml-org** `llama-server.exe` (Windows CPU build, tag `b10988`) into `engine/`, or
   let `INSTALL.bat` fetch it. The console never uses a nested Ollama copy.
2. `INSTALL.bat` — seeds **your** Soul / Identity / Memory. No steward identity is included.
3. `LYGO_LLM_CONSOLE.bat` — the launcher is drive-portable (`%~dp0`): it runs *this* folder, whatever
   drive it sits on, and refuses to start a second console on the same ports.
4. Open <http://127.0.0.1:9641/> and pick a model.

Run it as a normal, **unprivileged** user. Default bind is loopback (`127.0.0.1`); a LAN bind needs
`--lan --i-consent`.

## What it can do (and what it cannot)

Can: scan drives for GGUF files and read-only Ollama CAS trees, boot a local llama.cpp server on a
private loopback port, serve a browser portal, run allowlisted limbs (files, memory, search, fetch,
RAG over your own corpus, images when a projector is registered), gate every generation through the
LYGO P0 Φ-gate, and speak a subset of the OpenAI HTTP shape on `/v1/*`.

Cannot: reach the steward's drives, vaults or keys; publish anything; call `ollama.exe`; write
outside this kit's `workspace/` and `save/` unless you deliberately widen it in config.

Page: <https://chatagent.ca/lygo-llm-console.html> · ClawHub: <https://clawhub.ai/deepseekoracle/skills/lygo-llm-console>
