# Quickstart

```bash
npx --yes clawhub@0.23.3 install deepseekoracle/lygo-llm-console
cd lygo-llm-console
python scripts/self_check.py
python scripts/verify_kit.py
```

Verification checks every file in `kit/` against `kit/KIT_SHA256SUMS.txt` (152 lines) and confirms the
count in `kit/PUBLIC_KIT.json`. If it fails, stop.

```bash
# 1. engine: ggml-org CPU llama-server, tag b11074, into kit/engine/
#    (or run kit/INSTALL.bat and let it fetch)
# 2. seed your own identity (writes only inside kit/)
cd kit && python src/install.py

# 3. start it as an unprivileged user, then open http://127.0.0.1:9641/
```

On Windows: `kit/INSTALL.bat`, then `kit/LYGO_LLM_CONSOLE.bat`. Stop it with
`kit/LYGO_LLM_CONSOLE_STOP.bat`, which frees only ports held by the console's own processes.
