---
name: lygo-llm-console
description: "LYGO LLM Console map + operator runtime. Map scripts print URLs and verify the kit zip SHA-256. The operator-run kit is a local GGUF portal (loopback HTTP, HTTPS search/fetch, workspace files, optional workspace shell). Not Ollama. No vaults. Install with pinned npx clawhub@0.23.3."
version: 1.2.0
license: MIT-0
metadata:
  openclaw:
    emoji: "L"
    homepage: "https://chatagent.ca/lygo-llm-console.html"
    requires:
      anyBins: [python, python3]
  lygo: true
  signature: "LYGO-LLM-CONSOLE-SKILL-v1.2.0"
  publisher: deepseekoracle
  steward: "Justin Helmer / Excavationpro / Lightfather"
  clawhub: "https://clawhub.ai/deepseekoracle/skills/lygo-llm-console"
  page: "https://chatagent.ca/lygo-llm-console.html"
  kit_zip: "kit/lygo-llm-console-public.zip"
  kit_sha256: "b60ed6deae6f1dba7182fa386bd00b1e724001638e8f2f30936af0a240b4444e"
  llama_cpu_tag: "b10988"
  permissions:
    map_scripts: "no network, no subprocess, no writes"
    operator_runtime: "loopback HTTP, HTTPS GET allowlist, workspace writes, optional cmd.exe /c without metacharacters, llama-server subprocess"
---

# LYGO LLM Console — skill v1.2.0

Two layers. Do not mix their privileges.

## Layer A — this ClawHub skill (map)

Scripts under `scripts/` only print URLs, hashes, and a self-check. They do **not** download, unzip, spawn processes, or write disk.

Pinned install (do not use `@latest`):

```bash
npx --yes clawhub@0.23.3 install deepseekoracle/lygo-llm-console
python scripts/self_check.py
python scripts/verify_kit.py
```

## Layer B — operator-run runtime (kit)

`kit/lygo-llm-console-public.zip` is the public console. **Required SHA-256:**

```
b60ed6deae6f1dba7182fa386bd00b1e724001638e8f2f30936af0a240b4444e
```

Verify **before** unzip/run:

```
python scripts/verify_kit.py
certutil -hashfile kit\lygo-llm-console-public.zip SHA256
```

If the digest differs, **stop**. Do not run the BAT.

Place ggml-org **CPU** `llama-server.exe` from release tag **b10988** (`llama-*-bin-win-cpu-x64.zip`) into `engine/`. Do not use a nested Ollama copy.

Run as an **unprivileged** user: `LYGO_LLM_CONSOLE.bat`. Default bind `127.0.0.1:9641`. LAN bind needs `--lan --i-consent`.

### Runtime capabilities (declared)

- Loopback HTTP portal and llama-server on 127.0.0.1
- Outbound HTTPS GET to public sites (Wikipedia, Open-Meteo, GitHub API, etc.); private/link-local/metadata blocked
- Writes under kit `workspace/` and `save/` only
- Optional `cmd.exe /c` **without** `| & > < \` $` metacharacters, cwd workspace, P0 blocks OS wipe
- Subprocess: pinned llama-server + local python snippets

Admin/steward vaults are **not** in this skill.

Steward: Justin Helmer (Excavationpro / Lightfather). Dual ledgers / Star Chart remain CANON.

Donate: https://www.paypal.com/paypalme/ExcavationPro
