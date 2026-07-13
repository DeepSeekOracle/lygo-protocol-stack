# LYGO Builder USB — Steward Tier Docs

**Signature:** `Δ9Φ963-BUILDER-STEWARD-v1`  
**Audience:** Lattice stewards and GROK_BUILDR instances — **not** PUBLIC_SKU retail zips.

These files document how the 32GB builder USB was constructed. Public buyers use [LYGO_USB_CHAMPION_V1_GENERIC.md](../LYGO_USB_CHAMPION_V1_GENERIC.md) and `BUILD_SELF_FIRST_USE.txt` inside the free zip.

| File | Purpose |
|------|---------|
| [FULL_BUILDR_USB_BUILDERS_BLUEPRINT.txt](./FULL_BUILDR_USB_BUILDERS_BLUEPRINT.txt) | Phase 1–3 build order, directory map, launchers |
| [GROK_BUILDR_BOOT.md](./GROK_BUILDR_BOOT.md) | Grok builder identity + session boot |
| [BUILD_SELF_FIRST_USE.txt](./BUILD_SELF_FIRST_USE.txt) | First-use Ollama/model setup (also ships in public zip) |

**Canonical narrative:** [LYGO_USB_AND_CLAW_MASTER_WHITEPAPER.md](../LYGO_USB_AND_CLAW_MASTER_WHITEPAPER.md)  
**Stack packer:** `tools/build_lygo_builder_key.py`  
**Dev overlay:** `I:\E Drive\LYGO_BUILDR_USB` → sync to `E:\LYGO_BUILDER_KEY`

**Never export:** `_builder_vault/`, `core_signing.key`, or any API/token backups.