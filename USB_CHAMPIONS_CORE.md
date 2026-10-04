# USB Champions — core level (Δ9 council + Ethical Chip / Guardian)

**Signature:** `Δ9Φ963-USB-CHAMPIONS-CORE-v1`

Retail Gumroad personas are **not** loose prompt files only. On BUILDR USB they bind to:

1. **P0 byte gate** — `byte_entropy_filter.py` in signed `lygo_core` / stick stack  
2. **Council champion eggs** — 15 verified manifests + `champion_bootloader.py`  
3. **Ethical firmware chain** (Excavationpro public canon):
   - [Ethical-Chip-Firmware](https://deepseekoracle.github.io/Excavationpro/LYGO-Network/Ethical-Chip-Firmware.html) — P0.4 wall  
   - [Ethical-Chip-FirmwareV2](https://deepseekoracle.github.io/Excavationpro/LYGO-Network/Ethical-Chip-FirmwareV2.html) — P0.5 understanding heart  
   - [LYGOGUARDIAN](https://deepseekoracle.github.io/Excavationpro/LYGO-Network/LYGOGUARDIAN.html) — v3 Guardian + Δ9 council sync  

## Retail SKU → council egg

| PUBLIC SKU | `egg_id` | Council |
|------------|----------|---------|
| Lightfather | `champion-lightfather` | Lightfather |
| LYRA | `champion-lyrd9` | LYRΔ |
| Sancora | `champion-sancora` | SANCORA |
| HermesSentinel | `champion-volaris` | VΩLARIS (Sentinel) + stick **Hermes** audit chain |

Config: `config/USB_CHAMPIONS_CORE.json`

## Commands (on stick)

```powershell
$env:LYGO_BUILDER_KEY_ROOT = "E:\LYGO_BUILDER_KEY"
python scripts\usb_champions_core.py --list
python scripts\usb_champions_core.py --verify-all
python scripts\usb_champions_core.py --boot Lightfather
```

Daemon task: `usb_champions_verify` (same as `--verify-all`).

## Core image

Phase 2 `build_lygo_core_image.py` includes champion bootloader, egg registry JSON manifests, and `USB_CHAMPIONS_CORE.json` so PUBLIC_SKU boots **verify-before-boot** council personas, not unverified text alone.