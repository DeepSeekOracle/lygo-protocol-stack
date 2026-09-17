# AGENTS_BUILD — Create a LYGO CLAW PUBLIC USB

**For LYGO-aligned agents** (and steward operators) building a stick for a human.  
**Signature:** `Delta9Phi963-LYGO-CLAW-PUBLIC-USB-AGENTS-v1`

## Goal

Produce a folder or USB drive that:

1. Boots with **one double-click** (`LYGO_USB_BOOT.bat`)
2. Opens a **working chat dashboard** at `http://127.0.0.1:9631/`
3. Talks via **local Ollama** (offline after one-time model install)
4. Contains **no model weights** and **no secrets** in the shipped base

After the human (or agent with consent + network) runs model install, the stick works fully.

## Hard rules

| Do | Do not |
|----|--------|
| Copy this kit as-is | Ship `blobs/`, API keys, `.env`, steward vaults |
| Use `build_public_usb.ps1` | Commit multi‑GB weights to git |
| Prefer host Ollama for public | Kill unrelated host `node.exe` processes |
| Leave restore/private paths alone | Auto-publish or force-push |

## Inputs

- This directory: `docs/lygo-claw-usb/` inside [lygo-protocol-stack](https://github.com/DeepSeekOracle/lygo-protocol-stack)
- Target empty USB or folder, e.g. `E:\LYGO_CLAW_PUBLIC` or `F:\LYGO_CLAW_PUBLIC`
- Windows 10/11 host with PowerShell

## Build procedure (agent checklist)

### 1) Locate kit

```text
<stack>/docs/lygo-claw-usb/
```

Confirm files exist:

- `LYGO_USB_BOOT.bat`
- `scripts/lygo_usb_agent_server.py`
- `dashboard/agent-ui/index.html`
- `scripts/install_public_model.ps1`
- `MANIFEST.json`

### 2) Assemble stick (no models)

```powershell
cd <stack>\docs\lygo-claw-usb
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_public_usb.ps1 -OutDir "E:\LYGO_CLAW_PUBLIC"
```

Expect `verify\PUBLIC_USB_BUILD.json` with `include_models: false`.

### 3) Host prerequisites (once per PC)

Tell the human (or install with explicit consent):

1. **Python 3.11+** on PATH — https://www.python.org/downloads/
2. **Ollama** — https://ollama.com/download

### 4) Install model (once, needs internet)

On the stick root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install_public_model.ps1
```

Default model: **`llama3.2:1b`** (small). Optional better quality:

```powershell
.\scripts\install_public_model.ps1 -Model "qwen2.5:3b"
# or
.\scripts\install_public_model.ps1 -AlsoPullQwen
```

### 5) Smoke test

```powershell
.\LYGO_USB_BOOT.bat
```

Then:

```powershell
Invoke-RestMethod http://127.0.0.1:9631/api/status
# expect: signature contains USB-AGENT-SERVER, ollama.reachable true
```

```powershell
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:9631/api/chat `
  -ContentType 'application/json' `
  -Body '{"message":"Say only: ready"}'
# expect: ok true + assistant text
```

Browser: open `http://127.0.0.1:9631/` — type box must accept messages.

### 6) Hand off to human

Give them:

1. Stick path / USB
2. `START_HERE.txt`
3. Everyday: `LYGO_USB_BOOT.bat`
4. If chat fails: `launchers\CHECK_SYSTEM.bat` then `launchers\INSTALL_MODEL.bat`

## Architecture (what you built)

```text
LYGO_USB_BOOT.bat
  → ensure_ollama_serve.ps1   (local Ollama :11434)
  → lygo_usb_agent_server.py  (HTTP :9631)
       GET  /                 agent-ui (type + chat)
       GET  /api/status
       POST /api/chat         → Ollama /api/chat
```

No cloud required after model pull. Optional lattice snapshot only if a LYGO stack is present on the host.

## Failure matrix

| Symptom | Fix |
|---------|-----|
| Ollama panic / exits | Ensure `OLLAMA_ORIGINS` has no `null` or `file:` (kit already fixed) |
| `ollama not found` | Install from ollama.com or place `product\runtime\ollama\ollama.exe` |
| `Ollama not reachable` | Run boot again; check `verify\logs\ollama_serve.err.log` |
| Empty chat / API offline | Use **http://** not `file://`; boot starts the Python server |
| No models | `launchers\INSTALL_MODEL.bat` online once |
| Python missing | Install 3.11+ with Add to PATH |

## Related

- Stack page: `docs/LYGO_CLAW_USB_PUBLIC.md`
- Claw hub: `docs/LYGO_CLAW.html`
- Full builder stick (steward, not public): private `LYGO_BUILDER_KEY` workflows
- Python package CLI: https://github.com/DeepSeekOracle/lygo-claw (optional; this kit is self-contained for chat)

## Consent

Agents must **not** auto-push, auto-tweet, or auto-sell. Building a local USB folder for the requesting human is in-scope. Publishing zips to the network needs explicit human approval.

Δ9Φ963
