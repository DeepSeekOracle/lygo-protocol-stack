---
name: lygo-llm-console
description: "Use when an operator wants a sovereign LOCAL LLM runtime instead of Ollama: scan GGUF on disk, boot llama.cpp on loopback, chat with an agent portal and allowlisted tools. Ships the public kit UNPACKED (v1.5.6, 152 files, per-file SHA-256) so every file that would run can be read first. Map scripts do no network, no subprocess, no writes; the kit itself listens on loopback, fetches public HTTPS, writes only inside its own folder, and can run workspace shell/Python (not a sandbox). No steward vaults, keys or weights. Pinned install: npx --yes clawhub@0.23.3 install deepseekoracle/lygo-llm-console. Do NOT use for cloud inference, for serving untrusted users, or where you cannot run Python as an unprivileged user."
version: 1.6.0
license: MIT-0
metadata:
  openclaw:
    emoji: "L"
    homepage: "https://chatagent.ca/lygo-llm-console.html"
    requires:
      anyBins: [python, python3]
    os: [windows, macos, linux]
  lygo: true
  signature: "LYGO-LLM-CONSOLE-SKILL-v1.6.0"
  publisher: deepseekoracle
  steward: "Justin Helmer / Excavationpro / Lightfather"
  clawhub: "https://clawhub.ai/deepseekoracle/skills/lygo-llm-console"
  page: "https://chatagent.ca/lygo-llm-console.html"
  console_release: "1.5.6"
  kit: "kit/ (unpacked public tree, ship form: no archive)"
  kit_files: 152
  kit_bytes: 2162433
  kit_sha256sums: "7b1188ca0a9c1fd81a34a53042506026efde944ba4d7b5f88bfcf225e6f8db8e"
  kit_manifest: "kit/PUBLIC_KIT.json"
  llama_cpu_tag: "b11074"
  clawhub_cli_pin: "clawhub@0.23.3"
  permissions:
    map_scripts: "no network, no subprocess, no shell, no writes; reads skill files only"
    operator_runtime_kit: "listens 127.0.0.1 (console 9641, engine 11441); outbound HTTPS GET only; writes kit workspace/ and save/; may spawn pinned llama-server.exe and local python -c; optional cmd.exe /c without metacharacters"
    lan_bind: "requires --lan --i-consent"
    publish: false
---

# LYGO LLM Console — skill v1.6.0 (ships console 1.5.6)

Two layers with different privileges. Do not read one as the other.

## Layer A — the map (this skill's scripts)

`scripts/` prints URLs, hashes and a self-check. No network, no subprocess, no shell, no disk writes.

```bash
npx --yes clawhub@0.23.3 install deepseekoracle/lygo-llm-console
python scripts/self_check.py          # declares what this package is and is not
python scripts/verify_kit.py          # verifies the unpacked kit, file by file
python scripts/lygo_llm_console_map.py plain
```

## Layer B — the operator runtime (`kit/`, unpacked)

`kit/` is the public console, **shipped as a tree rather than a zip on purpose**: a reviewer can read
every file that would run, and a scanner can read it too, instead of trusting a hash inside an archive
(the v1.2.0 package shipped a zip and drew four HIGH "referenced artifact was not completely inspected /
embedded NUL bytes" findings).

- `kit/VERSION` — `1.5.6` (the release this tree is)
- `kit/PUBLIC_KIT.json` — per-file SHA-256, the source tree, what was left out and why
- `kit/KIT_SHA256SUMS.txt` — 152 lines; `python scripts/verify_kit.py` checks every one

If verification fails, **stop**. Do not run the BAT.

Place ggml-org **CPU** `llama-server.exe` from release tag **b11074** (`llama-*-bin-win-cpu-x64.zip`)
into `kit/engine/` (or let `INSTALL.bat` fetch it). Do not point it at a nested Ollama copy.

Run it as an **unprivileged** user: `kit/INSTALL.bat` once (seeds *your* identity), then
`kit/LYGO_LLM_CONSOLE.bat`. The launcher resolves its own folder (`%~dp0`) — it runs the kit you
verified wherever it sits — and it will not start a second console on the same ports. Portal:
<http://127.0.0.1:9641/>, engine on `127.0.0.1:11441`. A LAN bind needs `--lan --i-consent`.

### Declared capabilities (measured on 1.5.6, not aspirational)

- **Listen:** loopback HTTP only by default. 9641 portal, 11441 engine. LAN requires consent flags.
- **Network out:** HTTPS GET to public hosts (Wikipedia, Open-Meteo, GitHub, arXiv, HN, Wayback, Jina,
  HuggingFace, ClawHub search). Private, link-local, loopback, `.local` and `.internal` hosts are
  refused by name and by range, and only `https` is accepted.
- **Files:** writes under the kit's own `workspace/` and `save/` unless the operator maps more in
  `config/console.json`. `save_note` to Desktop/Documents/Downloads/home asks for consent first.
- **Processes:** spawns the pinned `llama-server.exe`, and local `python -c` / `cmd.exe /c` snippets.
- **Honest limit — this is NOT a sandbox.** `shell`, `python_exec`, `rust_exec` and `cargo` limbs run
  code as *your* user inside the kit folder: metacharacter rules and the LYGO P0 gate refuse obvious
  destructive shapes (wipe, credential reads), but nothing stops arbitrary local code. Treat the kit
  as code you are choosing to run, exactly as the source you just read implies.
- **State it keeps:** `workspace/` identity and notes, `save/` sessions, receipts, RAG index, model
  registry, a local API token in `data/`, and background threads while the server runs.
- **The full limb registry is present** in a public kit, including the admin-map-shaped names
  (`steward_map`, `self_check`, `self_seal`). Measured on a clean unpacked copy: the admin map answers
  `role: "public_kit"` with `drives: {}` and only the kit's own read/write roots — no steward data
  exists to return. Do not describe those limbs as steward access.

### What it does not do

- No model weights, no `llama-server.exe`, no `engine/` binaries, no saved images in this package.
- No steward vaults, keys, admin `config/admin.json`, `config/api.json`, no other kit's model store.
- No `ollama.exe` — importing an existing Ollama CAS tree is optional and read-only.
- No auto-publish, no telemetry, no auto-update. Nothing in the kit leaves your machine by itself.

## When not to use this

- You want cloud inference, a hosted API, or a shared multi-user service.
- You cannot run Python and a local process as an unprivileged user.
- You need a hard sandbox: the console runs local shell/Python on purpose, and says so above.
- You need CANON of the LYGO lattice. This kit is RESOURCE; dual ledgers and the Haven Star Chart are
  CANON and are not in scope here.

## Removal

Delete the installed skill folder and the kit folder it created (its `workspace/`, `save/`, `data/`
live inside that folder). Stop the console with `kit/LYGO_LLM_CONSOLE_STOP.bat`, which frees only
ports held by the console's own `python.exe` / `llama-server.exe`.

See `references/SECURITY.md`, `references/PUBLIC_VS_ADMIN.md`, `references/WHAT_CHANGED_1_6_0.md`.

Steward: Justin Helmer (Excavationpro / Lightfather). Built with LYGO AI agents. Inference by
ggml-org llama.cpp (operator-supplied binary). Donate: https://www.paypal.com/paypalme/ExcavationPro
