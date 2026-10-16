# BUILDR USB — standalone inference

**Master running log (USB + LYGO-Claw):** [LYGO_USB_AND_CLAW_MASTER_WHITEPAPER.md](./LYGO_USB_AND_CLAW_MASTER_WHITEPAPER.md)

**Profile:** `SOVEREIGN_FAST` → `qwen2.5:3b` stored under `product/models/ollama` on the stick.

## One-boot (Ollama + model on USB)

Builder machine once:

```powershell
E:\LYGO_BUILDER_KEY\scripts\bundle_ollama_to_usb.ps1
E:\LYGO_BUILDER_KEY\scripts\hydrate_usb_models.ps1
```

Any PC:

```text
E:\LYGO_BUILDER_KEY\launchers\LYGO_One_Boot_AI.bat
```

Fallback if runtime not bundled: `install_usb_runtime.ps1` + `LYGO_Standalone_AI.bat`

`bootstrap_env.ps1` sets `OLLAMA_MODELS` to the USB path so weights travel with the drive.

## Verify

```powershell
python E:\LYGO_BUILDER_KEY\scripts\verify_standalone_usb.py
```

Overlay: `I:\E Drive\LYGO_BUILDR_USB\product\models\STANDALONE_MODEL_DESIGN.md`