# Excavationpro Music Kernel Egg

**egg_id:** excavationpro-music-catalog-v1  
**ISRCs:** 718  
**content_sha256:** `a2cda0c3e292ed1167c8e6be21524fca103c55b04a7fdba98c3610c9d494528c`  
**size:** 42536 bytes

## Expand workflow
1. Drop masters with ISRC in filename under `J:\ALL SOUND FILES\...\0 DONE ALBUM` (or any scanned root)
2. Update DistroKid restore list if needed
3. `python tools/music_catalog_recovery.py` and/or re-scan DONE ALBUM
4. `python tools/build_music_registry_site.py`  (updates expandable HTML + ledger JSON)
5. `python tools/_make_music_egg_payload.py`
6. `python tools/build_kernel_eggs.py --egg excavationpro-music-catalog-v1`
7. Plant with consent: `plant_with_consent.py --i-consent ...`

Public page: loads `data/excavationpro_music_ledger.json` so new releases appear after rebuild without redesigning HTML.
