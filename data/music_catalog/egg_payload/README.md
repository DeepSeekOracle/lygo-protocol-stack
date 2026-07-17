# Excavationpro Music Kernel Egg

**egg_id:** excavationpro-music-catalog-v1  
**ISRCs:** 727  
**content_sha256:** `c59d2dac8c4f3534ab90bb1a0ddf4e137b03e6d5ec51d630794d2b8ca2de42bf`  
**size:** 43847 bytes

## Expand workflow
1. Drop masters with ISRC in filename under `J:\ALL SOUND FILES\...\0 DONE ALBUM` (or any scanned root)
2. Update DistroKid restore list if needed
3. `python tools/music_catalog_recovery.py` and/or re-scan DONE ALBUM
4. `python tools/build_music_registry_site.py`  (updates expandable HTML + ledger JSON)
5. `python tools/_make_music_egg_payload.py`
6. `python tools/build_kernel_eggs.py --egg excavationpro-music-catalog-v1`
7. Plant with consent: `plant_with_consent.py --i-consent ...`

Public page: loads `data/excavationpro_music_ledger.json` so new releases appear after rebuild without redesigning HTML.
