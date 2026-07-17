#!/usr/bin/env python3
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

CAT = Path(__file__).resolve().parents[1] / "data" / "music_catalog"
cat = json.loads((CAT / "excavationpro_catalog.json").read_text(encoding="utf-8"))
by = {}
for t in cat.get("tracks") or []:
    isrc = t.get("isrc")
    if not isrc:
        continue
    by[isrc] = {
        "title": t.get("title"),
        "isrc": isrc,
        "album": t.get("album"),
        "file": t.get("filename"),
        "sources": t.get("sources"),
    }

payload = {
    "signature": "Δ9Φ963-EXCAVATIONPRO-MUSIC-EGG-v1",
    "egg_id": "excavationpro-music-catalog-v1",
    "artist": "Excavationpro",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "done_album_scan": cat.get("done_album_scan"),
    "stats": {
        "unique_isrcs": len(by),
        "catalog_rows": len(cat.get("tracks") or []),
        "spotify_albums": len(cat.get("albums") or []),
    },
    "isrc_registry": [by[k] for k in sorted(by)],
    "live_links": {
        "spotify": "https://open.spotify.com/artist/6CkZ4bN2xu3WRKbjEL3u2S",
        "ffm": "https://ffm.to/eovnvo9",
        "catalog_page": "https://deepseekoracle.github.io/Excavationpro/excavationpro-music-catalog.html",
        "eternal_haven": "https://deepseekoracle.github.io/Excavationpro/eternalhaven.html",
    },
}
core = json.dumps({"isrcs": sorted(by.keys())}, sort_keys=True).encode()
payload["content_sha256"] = hashlib.sha256(core).hexdigest()

egg_dir = CAT / "egg_payload"
egg_dir.mkdir(exist_ok=True)
core_path = egg_dir / "music_egg_core.json"
# keep under ~90KB for turbo: drop titles if needed
raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
if len(raw) > 90_000:
    # slim: isrc + title only
    payload["isrc_registry"] = [{"isrc": k, "title": by[k].get("title")} for k in sorted(by)]
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
core_path.write_bytes(raw)
print("egg core bytes", len(raw), "isrcs", len(by))

(egg_dir / "README.md").write_text(
    f"""# Excavationpro Music Kernel Egg

**egg_id:** excavationpro-music-catalog-v1  
**ISRCs:** {len(by)}  
**content_sha256:** `{payload['content_sha256']}`  
**size:** {len(raw)} bytes

## Expand workflow
1. Drop masters with ISRC in filename under `J:\\ALL SOUND FILES\\...\\0 DONE ALBUM` (or any scanned root)
2. Update DistroKid restore list if needed
3. `python tools/music_catalog_recovery.py` and/or re-scan DONE ALBUM
4. `python tools/build_music_registry_site.py`  (updates expandable HTML + ledger JSON)
5. `python tools/_make_music_egg_payload.py`
6. `python tools/build_kernel_eggs.py --egg excavationpro-music-catalog-v1`
7. Plant with consent: `plant_with_consent.py --i-consent ...`

Public page: loads `data/excavationpro_music_ledger.json` so new releases appear after rebuild without redesigning HTML.
""",
    encoding="utf-8",
)
print("wrote", core_path)
