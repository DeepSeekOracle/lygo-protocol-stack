# LYGO CLAW PUBLIC USB

**Working offline agent dashboard + chat** base kit for Windows.  
**No model weights. No secrets.** Version **1.2**.

| | |
|--|--|
| Boot | `LYGO_USB_BOOT.bat` |
| Chat UI | http://127.0.0.1:9631/ |
| Agent instructions | [AGENTS_BUILD.md](./AGENTS_BUILD.md) |
| Humans | [START_HERE.txt](./START_HERE.txt) |
| Manifest | [MANIFEST.json](./MANIFEST.json) |

## Quick start

1. Copy this folder to a USB or disk path  
2. Install [Python 3.11+](https://www.python.org/downloads/) + [Ollama](https://ollama.com/download)  
3. `launchers\INSTALL_MODEL.bat` (pulls `llama3.2:1b`)  
4. `LYGO_USB_BOOT.bat` → type in the browser  

## Agents

Follow **[AGENTS_BUILD.md](./AGENTS_BUILD.md)** to assemble a stick for a human:

```powershell
powershell -File .\scripts\build_public_usb.ps1 -OutDir E:\LYGO_CLAW_PUBLIC
```

## Repo location

Shipped inside [lygo-protocol-stack](https://github.com/DeepSeekOracle/lygo-protocol-stack):

```text
docs/lygo-claw-usb/
```

Pages / docs entry: [LYGO_CLAW_USB_PUBLIC.md](../../docs/LYGO_CLAW_USB_PUBLIC.md)

Δ9Φ963
