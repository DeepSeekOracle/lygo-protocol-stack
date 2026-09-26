# BUILDR USB Phase 3 — PUBLIC_SKU (Gumroad)

**Prerequisite:** Phase 2 gate `all_ok` on `E:\LYGO_BUILDER_KEY`.

## Export one SKU

```powershell
E:\LYGO_BUILDER_KEY\scripts\export_public_sku.ps1 -Champion Lightfather -OutDir "I:\E Drive\LYGO_BUILDR_EXPORTS\Lightfather"
```

## Export all four champions

```powershell
E:\LYGO_BUILDER_KEY\scripts\build_phase3_all_skus.ps1
```

## Verify export (no secrets)

```powershell
python E:\LYGO_BUILDER_KEY\scripts\verify_public_sku.py "I:\E Drive\LYGO_BUILDR_EXPORTS\Lightfather"
```

## Ship checklist

- [ ] `PUBLIC_MANIFEST.json` + `README.txt` + `LICENSE.txt`
- [ ] `images/lygo_core.tar.gz` + `.sha256` (no `_builder_vault` / no `.sig` key)
- [ ] Active `champions/<name>/`
- [ ] Zip for Gumroad; steward listing per `PUBLIC_SKU_GUMROAD.md` on stick

Overlay source: `I:\E Drive\LYGO_BUILDR_USB\`

Δ9Φ963