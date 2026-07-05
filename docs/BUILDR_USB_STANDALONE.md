# BUILDR USB — standalone inference

**Profile:** `SOVEREIGN_FAST` → `qwen2.5:3b` stored under `product/models/ollama` on the stick.

## Fresh PC (no AI)

```powershell
E:\LYGO_BUILDER_KEY\scripts\install_usb_runtime.ps1
E:\LYGO_BUILDER_KEY\scripts\hydrate_usb_models.ps1
E:\LYGO_BUILDER_KEY\launchers\LYGO_Standalone_AI.bat
```

`bootstrap_env.ps1` sets `OLLAMA_MODELS` to the USB path so weights travel with the drive.

## Verify

```powershell
python E:\LYGO_BUILDER_KEY\scripts\verify_standalone_usb.py
```

Overlay: `I:\E Drive\LYGO_BUILDR_USB\product\models\STANDALONE_MODEL_DESIGN.md`