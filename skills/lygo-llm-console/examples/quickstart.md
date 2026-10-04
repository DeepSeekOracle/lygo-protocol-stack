# Quickstart

```bash
npx --yes clawhub@0.23.3 install deepseekoracle/lygo-llm-console
python scripts/self_check.py
python scripts/verify_kit.py
```

Unzip `kit/lygo-llm-console-public.zip` only after the SHA-256 matches.

Place `llama-server.exe` from ggml-org tag b10988 into `engine/`.

Run `LYGO_LLM_CONSOLE.bat` as a normal (non-admin) user.
