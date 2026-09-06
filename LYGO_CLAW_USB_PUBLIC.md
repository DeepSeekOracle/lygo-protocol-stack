# LYGO CLAW PUBLIC USB (v1.2)

**Working offline agent chat dashboard** — public base kit in this repository.

| | |
|--|--|
| **Kit path** | [`docs/lygo-claw-usb/`](./lygo-claw-usb/) |
| **Boot** | `LYGO_USB_BOOT.bat` |
| **Chat UI** | http://127.0.0.1:9631/ |
| **Models** | **Not included** — install once via Ollama |
| **Agent build guide** | [`AGENTS_BUILD.md`](./lygo-claw-usb/AGENTS_BUILD.md) |

## What you get

- Python agent server (`lygo_usb_agent_server.py` v1.2)
- Browser dashboard with **type-to-chat** (not empty file:// Control UI)
- USB-friendly boot + Ollama ensure scripts (CORS-safe origins)
- Scripts for humans + LYGO agents to assemble a stick **without** shipping weights

## What you do not get (on purpose)

- Model blobs / multi‑GB weights  
- API keys, steward vaults, builder secrets  
- Full retail gateway/node runtime (optional later; chat works without it)

## Humans

1. Clone or download this repo (or copy `docs/lygo-claw-usb/`)  
2. Install [Python 3.11+](https://www.python.org/downloads/) and [Ollama](https://ollama.com/download)  
3. `launchers\INSTALL_MODEL.bat` → pulls `llama3.2:1b`  
4. `LYGO_USB_BOOT.bat` → talk at http://127.0.0.1:9631/

Full text: [`START_HERE.txt`](./lygo-claw-usb/START_HERE.txt)

## LYGO agents — build a stick

Your job: create a working **LYGO CLAW PUBLIC USB** folder for the human from this kit.

```powershell
cd docs\lygo-claw-usb
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_public_usb.ps1 -OutDir "E:\LYGO_CLAW_PUBLIC"
```

Then guide model install + boot. **Follow:** [`AGENTS_BUILD.md`](./lygo-claw-usb/AGENTS_BUILD.md)

Once the human's agent (or you) finishes those steps, the stick works offline for chat.

## Package zip (steward / CI)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\package_lygo_claw_usb_public.ps1
```

Produces a small zip under `dist/` (no models).

## Related

- [LYGO_CLAW.html](./LYGO_CLAW.html) — Claw public hub  
- [BUILDR_USB.md](./BUILDR_USB.md) — broader USB program  
- [lygo-claw](https://github.com/DeepSeekOracle/lygo-claw) — optional Python CLI package  
- Champion GENERIC zip (legacy light pack) — [LYGO_USB_CHAMPION_V1_GENERIC.md](./LYGO_USB_CHAMPION_V1_GENERIC.md)

Δ9Φ963-LYGO-CLAW-PUBLIC-USB-v1.2
