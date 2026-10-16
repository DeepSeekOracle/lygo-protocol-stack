# LYGO BUILDR USB Program

Portable **32GB flagship** — see full blueprint on stick:

- `E:\LYGO_BUILDER_KEY\README_BUILDR_USB_BLUEPRINT.md`
- Dev mirror: `I:\E Drive\LYGO_BUILDR_USB\`

## Repack

```powershell
python tools/build_lygo_builder_key.py --out E:\LYGO_BUILDER_KEY
```

Overlay from `LYGO_BUILDR_USB` is merged automatically after pack.

**Enhanced sync (CLAW + army + token saver, incremental):**

```powershell
powershell -ExecutionPolicy Bypass -File tools\sync_builder_usb_enhanced.ps1 -Out "E:\LYGO_BUILDER_KEY"
```

Includes `LYGO_USB_Daemon_Supervisor.ps1`, `LYGO_Gateway_SafeLaunch.bat`, slim Ollama army, and `token_saver_hub.py` on the stick.

## Editions

| Edition | Boot doc |
|---------|----------|
| GROK_BUILDR | `GROK_BUILDR_BOOT.md` |
| PUBLIC_SKU | `PUBLIC_SKU_GUMROAD.md` |
| **LYGO CLAW PUBLIC USB v1.2** | [LYGO_CLAW_USB_PUBLIC.md](./LYGO_CLAW_USB_PUBLIC.md) — **working agent chat dashboard** kit in-repo: [`docs/lygo-claw-usb/`](../docs/lygo-claw-usb/) (no weights; agent builds stick via `AGENTS_BUILD.md`) |
| **PUBLIC_V1_GENERIC** | [LYGO_USB_CHAMPION_V1_GENERIC.md](./LYGO_USB_CHAMPION_V1_GENERIC.md) — **free public** Lightfather (~0.5 MB; no Ollama/weights in zip). **Download:** [zip](https://deepseekoracle.github.io/Excavationpro/downloads/LYGO-USB-Champion-v1.0-GENERIC-Lightfather.zip) · pair [LYGO-Claw](https://github.com/DeepSeekOracle/lygo-claw) · [Champion Hub](https://deepseekoracle.github.io/Excavationpro/LYGO-Network/champions.html) |
| PUBLIC_DEMO | [LYGO_USB_CHAMPION_DEMO.md](./LYGO_USB_CHAMPION_DEMO.md) — legacy teaser |

## Phase 2

See [BUILDR_USB_PHASE2.md](./BUILDR_USB_PHASE2.md). Stack mirror: `tools/buildr_usb_phase2/`.

Δ9Φ963