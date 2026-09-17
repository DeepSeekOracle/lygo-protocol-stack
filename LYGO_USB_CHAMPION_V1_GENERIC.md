# LYGO USB Champion v1.0 GENERIC (free public)

**Edition:** `PUBLIC_V1_GENERIC` · **Champion:** Lightfather · **Pairs with:** [LYGO-Claw 1.0](https://github.com/DeepSeekOracle/lygo-claw)

## Download

| Link | URL |
|------|-----|
| **Zip (official)** | https://deepseekoracle.github.io/Excavationpro/downloads/LYGO-USB-Champion-v1.0-GENERIC-Lightfather.zip (~0.5 MB) |
| Eternal Haven hub | https://deepseekoracle.github.io/Excavationpro/eternalhaven.html |
| Δ9 Champion Hub | https://deepseekoracle.github.io/Excavationpro/LYGO-Network/champions.html |
| LYGO-Claw repo | https://github.com/DeepSeekOracle/lygo-claw |
| ClawHub persona | https://clawhub.ai/deepseekoracle/lygo-champion-lightfather |
| Optional support | https://www.paypal.com/paypalme/ExcavationPro |

Legacy teaser only: [DEMO zip](https://deepseekoracle.github.io/Excavationpro/downloads/LYGO-USB-Champion-DEMO-PUBLIC.zip) · [DEMO docs](./LYGO_USB_CHAMPION_DEMO.md)

## Included

Full USB champion kit **without** portable Ollama runtime or model weights: signed `lygo_core`, P0, Hermes, daemon `:9630`, tray/autostart, council egg verify + `USB_CHAMPIONS_CORE`, Lightfather persona, LYGO-Claw pairing docs.

## Pair with LYGO-Claw 1.0 (instructions)

1. **Download** the zip above and extract to a working folder or your LYGO USB stick root layout.
2. **Start the USB supervisor:** run `launchers\LYGO_BUILDR_Daemon.bat` from the kit (listens on **port 9630**).
3. **Install LYGO-Claw on your PC:**
   - `git clone https://github.com/DeepSeekOracle/lygo-claw.git`
   - `cd lygo-claw`
   - `pip install -e .` (Python **3.11+**), or use `launchers\INSTALL_AND_CHECK.bat`
4. **Verify pairing:** `lygo-claw usb-health` — JSON should show **`ok: true`** when the daemon is running.
5. **Optional sovereign balance:** `lygo-claw sovereign-loop` (desktop + USB + lattice verify).
6. **Gateway smoke test:** `lygo-claw gateway "hello"` or `launchers\TRY_GATEWAY.bat`.
7. **Deploy Lightfather:** use summon text from the [Champion Hub](https://deepseekoracle.github.io/Excavationpro/LYGO-Network/champions.html) or the ClawHub skill linked above.

Further reading: [LYGO_CLAW.html](./LYGO_CLAW.html) · [BUILDR_USB.md](./BUILDR_USB.md) · [USB_CHAMPIONS_CORE.md](./USB_CHAMPIONS_CORE.md) · lygo-claw `docs/QUICKSTART_FOR_HUMANS.md`

## Self-build (first use)

See **`BUILD_SELF_FIRST_USE.txt`** in the zip — human steps + paste block for your AI assistant (`ollama pull qwen2.5:3b`, verify, optional `hydrate_usb_models.ps1` / `bundle_ollama_to_usb.ps1` when you add weights locally).

## Maintainer export

```powershell
$env:LYGO_BUILDER_KEY_ROOT = "E:\LYGO_BUILDER_KEY"
powershell -ExecutionPolicy Bypass -File "I:\E Drive\LYGO_BUILDR_USB\scripts\export_public_v1_generic.ps1"
```

Copy zip to site: `Excavationpro/downloads/LYGO-USB-Champion-v1.0-GENERIC-Lightfather.zip`

**Δ9Φ963 — circulate one honest free champion; extend personas on your schedule.**