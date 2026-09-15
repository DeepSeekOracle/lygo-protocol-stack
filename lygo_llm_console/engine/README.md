# Engine binaries (not in git)

Place official ggml-org llama.cpp Windows CPU zip contents here:

- `llama-server.exe`
- matching ggml / runtime DLLs

**Pin:** `b10988` (`llama-b10988-bin-win-cpu-x64.zip`)

Asset regex (CPU only): `^llama-.*-bin-win-cpu-x64\.zip$`

Never use `U:\LYGO\projects\ollama\lib\ollama\llama-server.exe`.
Never fetch `*-cuda-*` as the stream default.

Optional: `..\scripts\fetch_engine.ps1`
