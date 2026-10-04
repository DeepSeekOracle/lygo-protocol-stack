# LYGO LLM Console - public kit

A local, sovereign LLM runtime and agent portal. Not Ollama, and not the steward's
admin tree: no vaults, no keys, no model weights, no personal workspace.

## Run it

1. `INSTALL.bat` - seeds **your** Soul / Identity / Memory and checks python.
2. Put ggml-org CPU `llama-server.exe` in `engine/`, or run
   `powershell -File scripts\fetch_engine.ps1`.
3. `LYGO_LLM_CONSOLE.bat` - the launcher resolves its own folder (`%~dp0`), so it runs
   *this* copy wherever you unpacked it, and it refuses a second console on the same
   ports. Stop it with `LYGO_LLM_CONSOLE_STOP.bat`.
4. Open http://127.0.0.1:9641/ and pick a model.

Default bind is loopback (`127.0.0.1`); a LAN bind needs `--lan --i-consent`. Run it as a
normal, unprivileged user.

## What it can and cannot do

Can: scan drives for GGUF, boot a local llama.cpp server on a private loopback port,
serve a browser portal, run allowlisted limbs (files, memory, search, fetch, RAG over
your own corpus, images when a projector is registered), gate every generation through
the LYGO P0 check, and speak a subset of the OpenAI HTTP shape on `/v1/*`.

Cannot: reach the steward's drives, vaults or keys; publish anything; require Ollama;
write outside this folder's `workspace/` and `save/` unless you widen it in config.
The shell and Python limbs run code as *your* user - this is not a sandbox.

Page: https://chatagent.ca/lygo-llm-console.html
Source: https://github.com/DeepSeekOracle/lygo-protocol-stack
