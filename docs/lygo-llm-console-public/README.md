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


## Public kit

This zip is the **public** channel. Run **INSTALL.bat** first (seeds Soul / Identity / Memory for this user). It is not the steward admin tree. Write roots stay inside this folder until you Add Workspace access. Place ggml-org `llama-server.exe` in `engine/` (CPU Windows zip) or let INSTALL fetch it. Page: https://chatagent.ca/lygo-llm-console.html

## License and brand

**LYGO PC LOCAL CONSOLE™ is a branded product. Not open source, not MIT.** Licensed under the
**LYGO Sovereign License v3.0** (`Δ9Φ963-LICENSE-v3.0`): you may **use** it and **build on** it; you may
**not** sell it, rebrand it, white-label it, publish modified copies, or strip attribution, seals or
signatures.

- `LICENSE` — the terms (controlling text)
- `LICENSING.md` — plain English: yes-you-may / no-you-may-not, certified builds, the succession lock
- `TRADEMARKS.md` — the marks and how a fork must be named
- `NOTICE` — attribution, integrity rules, third-party licences (engine, model weights, vendored OpenClaw MIT)
- `SUCCESSION.md` — who holds the name and the seals if the Steward cannot
- `scripts/certify_build.py` — run it to check a copy: **CERTIFIED** or **MODIFIED**

**No license is retroactive:** earlier releases keep the license they shipped under for the copies
already distributed. This and every future release is v3.0. Steward: Justin Helmer
(Lightfather · Excavationpro · DeepSeekOracle).
