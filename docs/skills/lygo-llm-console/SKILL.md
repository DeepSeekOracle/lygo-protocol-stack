---
name: lygo-llm-console
description: "LYGO LLM Console — public ClawHub map to the sovereign local LLM runtime (not Ollama). Prints install path and download URL for the public kit. Windows-first portal for GGUF scan, chat, tools, images. Admin/steward tree is a separate channel and is not this package. Pure local. No network, no subprocess. Install clawhub:@deepseekoracle/lygo-llm-console."
version: 1.0.0
license: MIT-0
metadata:
  openclaw:
    emoji: "🜂"
    homepage: "https://chatagent.ca/lygo-llm-console.html"
    requires:
      anyBins: [python, python3]
  lygo: true
  llm: true
  console: true
  dual_channel: true
  signature: "Δ9Φ963-LYGO-LLM-CONSOLE-SKILL-v1.0.0"
  publisher: deepseekoracle
  steward: "Justin Helmer / Excavationpro / Lightfather"
  clawhub: "https://clawhub.ai/deepseekoracle/skills/lygo-llm-console"
  page: "https://chatagent.ca/lygo-llm-console.html"
  public_zip: "lygo-llm-console-public.zip"
  admin_tree: "lygo_llm_console/ (stack, not this skill)"
  permissions:
    network: false
    shell: false
    subprocess: false
    filesystem:
      read: "skill files only"
      write: false
    publish: false
---

# LYGO LLM Console — public tentacle v1.0.0

**Sovereign local LLM runtime + agent portal. Not Ollama. Not the admin tree.**

This ClawHub package is a **map**. It does **not** ship llama.cpp binaries, GGUF weights, steward vaults, or the admin console that lives on the steward disk.

Download and run the **public kit** from the studio page:

### → https://chatagent.ca/lygo-llm-console.html  
### → file **`lygo-llm-console-public.zip`** (SHA-256 on that page)

**Signature:** `Δ9Φ963-LYGO-LLM-CONSOLE-SKILL-v1.0.0`  
**ClawHub:** `@deepseekoracle/lygo-llm-console`  
**Mark:** LYGO® project family — steward Justin Helmer (Excavationpro / Lightfather). Built with LYGO AI agents. Dual ledgers / Haven Star Chart remain **CANON**; this skill is **RESOURCE**.

---

## Dual channel (honest)

| Channel | What you get |
|---------|----------------|
| **This skill (ClawHub)** | Map, credits, public vs admin, print URLs. No spawn. No network. |
| **Public kit zip** | Windows portal on `127.0.0.1:9641`, GGUF scan, P0 gate, kit-only tools, OpenAI-shaped `/v1` proxy. Vendored ggml-org `llama-server` is **fetched by the operator**, not bundled. |
| **Admin / steward** | `lygo-protocol-stack/lygo_llm_console/` plus any stream-node copy. **Not published on ClawHub.** Vaults, write-roots, and operator keys stay off the public kit. |

---

## What the product is (for humans and agents)

LYGO LLM Console is a **local orchestrator**. It does not implement transformer math itself. It:

1. Scans disks for GGUF files and (read-only) Ollama CAS trees (`blobs/sha256-*` + manifests).  
2. Starts official **ggml-org llama.cpp** `llama-server` on a private loopback port.  
3. Serves a browser agent portal (text, optional images if a projector is registered, allowlisted tools).  
4. Runs the LYGO **P0 Φ-gate** (physics + policy) on every generation.  
5. Speaks a subset of the OpenAI HTTP shape so other local apps can point at it **instead of** `ollama.exe`.

It **never requires Ollama**. Importing existing Ollama blobs is optional and read-only. It **never** calls `ollama.exe`.

---

## Install this tentacle

```bash
npx clawhub@latest install deepseekoracle/lygo-llm-console
cd path/to/lygo-llm-console
python scripts/self_check.py
python scripts/lygo_llm_console_map.py plain
python scripts/lygo_llm_console_map.py urls
```

Then open https://chatagent.ca/lygo-llm-console.html and download the public zip yourself.

---

## Commands

| Command | Output |
|---------|--------|
| `plain` | Human-readable overview |
| `map` / `demo` | JSON: dual channel, credits, URLs |
| `urls` | Page + zip + ClawHub + donate |

No network, no subprocess, no disk writes.

---

## What this skill does *not* do

- Does **not** ship the runtime zip or `llama-server.exe`  
- Does **not** ship model weights  
- Does **not** include the admin console, vaults, or steward write-roots  
- Does **not** auto-download anything  
- Does **not** replace dual ledgers / Star Chart CANON  

---

## Credits

- **Steward / author:** Justin Helmer (Excavationpro), Lightfather seat on the LYGO lattice  
- **LYGO AI agents:** protocol stack, P0 gate, public kit assembly  
- **Inference engine (separate project):** ggml-org llama.cpp  
- Design notes may cite Grok (xAI) as **RESOURCE**, not CANON  

Donate: [PayPal.me/ExcavationPro](https://www.paypal.com/paypalme/ExcavationPro) · [Patreon](https://www.patreon.com/Excavationpro)

---

## Security

See `references/SECURITY.md` and `references/PUBLIC_VS_ADMIN.md`.

**Δ9Φ963 — public map · operator fetches the kit · admin stays off ClawHub.**
