# LYGO LLM Console

Complete local **agent portal**: boot GGUF models, chat, tools, HTTPS search/fetch. **Does not call `ollama.exe`.**

**Signature:** `Δ9Φ963-LYGO-LLM-CONSOLE-v1`  
**Page / zip:** https://chatagent.ca/lygo-llm-console.html  
**Git:** https://github.com/DeepSeekOracle/lygo-protocol-stack (folder `lygo_llm_console/`)  
**ClawHub map:** `npx clawhub@latest install deepseekoracle/lygo-llm-console`  
**Steward:** Justin Helmer (Excavationpro / Lightfather) · LYGO AI agents

This GitHub folder is the **public product** (portal, limbs, Wikipedia/search, P0 gate, 15 champions, Continuity tabs).  
`llama-server.exe`, GGUF weights, operator tokens, and steward vaults are **not** in git.

Whitepaper: [`docs/whitepapers/LYGO_LLM_CONSOLE_v1.md`](../docs/whitepapers/LYGO_LLM_CONSOLE_v1.md)

## Three systems, one console

The same console, three ways to run it. **One of them is always the one you are in** — health and
status say which, and every surface is labelled the same way.

| System | Where the kit lives | What answers | Reach it by |
|--------|--------------------|--------------|-------------|
| **USB LOCAL** | On the stick, in a pocket | The stick's own engine (CPU-proven, boots on any PC); the API boosts it when a host or question needs more | `LYGO_AGENT_STICK.bat` on the stick |
| **PC LOCAL** | On a PC / fixed disk | This PC's engine — GPU when present, CPU otherwise — same API boost on demand | `LYGO_LLM_CONSOLE.bat` |
| **WEB PORTAL (API ONLY)** | Nothing local | The online API through the public web portal — no engine, no disks, no local models | `PUBLIC_GATEWAY.bat` + https://chatagent.ca/portal/ |

What each system **is** — three separate systems that share one console:

* **USB LOCAL** — the **stand-alone USB agent**: everything onboard the stick, so it plugs in and
  plays and is mobile (the same stick, any PC).
* **PC LOCAL** — the **fully built admin console on this PC**; this is the build that will later be
  turned into a public version.
* **WEB PORTAL (API ONLY)** — the **internet web portal**: API-only and usable online as an easy API
  agent portal, already fully built, so people have a web page version.

Which one you are in is measured, not assumed: the Windows volume type of the drive holding the kit
decides USB vs PC, and whether a local engine booted decides LOCAL vs API-ONLY (`src/surface.py`).
Override on unusual hardware with `LYGO_SURFACE=usb` or `LYGO_SURFACE=pc`.

## Install (public — new machine)

### A. Zip

1. Download https://chatagent.ca/data/lygo-full-skills/dist/lygo-llm-console-public.zip  
2. Unzip. Double-click **`INSTALL.bat`**.  
3. Optional: let it fetch `llama-server.exe`, or drop a ggml-org **CPU** zip into `engine/` (pin `b10988`).  
4. Put GGUF files in `models/` (or Scan later).  
5. Double-click **`LYGO_LLM_CONSOLE.bat`** → http://127.0.0.1:9641/

### B. Git (sparse, Windows)

```bat
git clone --depth 1 --filter=blob:none --sparse https://github.com/DeepSeekOracle/lygo-protocol-stack.git
cd lygo-protocol-stack
git sparse-checkout set lygo_llm_console
cd lygo_llm_console
INSTALL.bat
LYGO_LLM_CONSOLE.bat
```

`INSTALL.bat` seeds **your** Soul / Identity / Memory from `prompts/` (the human at this machine). It does **not** copy steward drives, vaults, or `admin.json`.

Add extra folders in the left-rail **Workspace** panel after boot.

Python 3 is required (`py` or `python`). No npm. No pip. No Ollama required. Existing `%USERPROFILE%\.ollama\models` blobs can be imported read-only.

**LYGO Engine** (hybrid): one Boot path. GGUF → llama.cpp mmap/SSD + GPU layers. Colibri HF dirs → expert streaming. Planner uses onboard RAM/VRAM. `LYGO_ENGINE.md`.

## Boot

```bat
python -u src\server.py serve
```

Loopback does not need a query token. LAN bind needs `--lan --i-consent`.  
Private llama-server: `127.0.0.1:11441`.

## Agent portal

Continuity: **Soul / Identity / Memory** (three files). Skills: 15 Δ9 champions on/off. Workspace: add/remove folders. Scan → Boot GGUF. Tools include wiki/web, fetch, weather, GitHub, lattice handshake, notepad, champions.

Writes stay under `workspace/` and `save/` unless you add a Workspace mount. `shell` / `python_exec` are workspace-cwd and **P0-blocked**. Dual ledgers / Star Chart remain CANON; web hits are RESOURCE.

## Public vs admin

| Public (git folder + zip + INSTALL.bat) | Admin / steward only |
|--|--|
| `prompts/` seeds identity for the new operator | `config/admin.json` (gitignored) + local `workspace/` |
| Kit-folder roots until they Add access | Extra disks / keys never committed |
| `LYGO_LLM_CONSOLE.bat` uses `%~dp0` | Same BAT; admin.json unlocks steward map |
| GitHub `lygo_llm_console/` | Local `data/`, `save/`, `engine/*.exe` gitignored |

Donate: [PayPal.me/ExcavationPro](https://www.paypal.com/paypalme/ExcavationPro) · [Patreon](https://www.patreon.com/Excavationpro)  
Arcade: https://chatagent.ca/games/ · Crypt: https://chatagent.ca/games/lattice-crypt/

## Docs for whoever builds this next

- **`WHITEPAPER.md`** — the as-built record: folder map (§8), defect ledger + rules (§11), builder recipes (§12), roadmap (§14). The same file is archived as `LYGO_LLM_CONSOLE_v2_AS_BUILT.md` under `E:\LYGO_BUILDER_KEY\docs\` and `E:\LYGO_BUILDER_KEY\RECOVERY\`.
- **`BUILD_MANIFEST.json`** — machine-readable ports, routes, modules, tests, invariants; hand it to an AI agent together with the whitepaper.
- **`tools/make_index.py`** — regenerates Appendix B (the module/function index) after code changes.
- Credentials (`config/api.json`, `.env`, `save/registry.json`) are never committed, never copied to the USB and always `[REDACTED]` in documents. Agents build, verify and report; **the steward publishes**.

## License and brand — read before you ship this

**LYGO PC LOCAL CONSOLE™ is a branded product. Not open source, not MIT.** Licensed under the
**LYGO Sovereign License v3.0** (`Δ9Φ963-LICENSE-v3.0`): you may **use** it and **build on** it; you may
**not** sell it, rebrand it, white-label it, publish modified copies, or strip attribution, seals or
signatures.

| File | What it is |
|---|---|
| `LICENSE` | the terms — this is the controlling text |
| `LICENSING.md` | plain English: yes-you-may / no-you-may-not, certified builds, the succession lock |
| `TRADEMARKS.md` | the marks, the powered-by badge, how a fork must be named |
| `NOTICE` | attribution line, integrity/manifest rules, third-party licences (engine, model weights, vendored OpenClaw MIT) |
| `SUCCESSION.md` | who holds the name and the seals if the Steward cannot |
| `scripts/certify_build.py` | verify a copy against its manifests → **CERTIFIED** or **MODIFIED** (and what that means) |

**No license is retroactive:** anything published earlier under a more permissive license keeps that
license for the copies already distributed. This and every future release is v3.0.

An independent reimplementation that copies no LYGO code and carries none of the marks is welcome —
with attribution. Anything else: ask in writing. Silence is not permission.

Steward: Justin Helmer (Lightfather · Excavationpro · DeepSeekOracle).
