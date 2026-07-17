# EXCAVATIONPRO — Music Catalog Recovery

**Artist:** Excavationpro  
**Spotify:** https://open.spotify.com/artist/6CkZ4bN2xu3WRKbjEL3u2S  
**ffm:** https://ffm.to/eovnvo9  
**Purpose:** Rebuild ISRC / UPC / title / album / file map after DistroKid store restriction (email from Ania, Jul 15 2026).

## What you have here

| File | Use |
|------|-----|
| `excavationpro_catalog.csv` | **Primary spreadsheet** for re-upload to a new distributor |
| `excavationpro_catalog.json` | Full machine-readable registry |
| `excavationpro_albums.csv` | Spotify album list + track counts |
| `excavationpro_isrcs_unique.txt` | One ISRC per line (from local filenames) |
| `excavationpro_catalog.md` | Human-readable summary |
| `DISTROKID_VAULT_BROWSER_HELPER.md` | Console scripts while **logged into** DistroKid vault |

## How data was recovered

1. **Local disk (J:\\ + Music/Documents)** — audio files; many DistroKid downloads include ISRC in the filename (e.g. `Song Title QZS672411119.wav` → `QZ-S67-24-11119`).
2. **Public Spotify** — album + track titles/IDs currently visible on the artist page (not a complete historical dump of every takedown).
3. **DistroKid vault** — requires your login; use the browser helper to harvest remaining ISRC/UPC from vault pages.

## Important limitations

- DistroKid **cannot reverse** store bans via their account (per their email). Metadata export may still be requested from support.
- Spotify public pages **do not always expose ISRC/UPC** in HTML; local filenames are the main ISRC source here.
- Not every file on J: is a commercial release (beats, drafts, stems). Filter the CSV by `isrc` column for release-ready rows.
- Spotify artist page only listed **~22 albums/singles** in this scrape — you may have far more live or previously live releases. Use DistroKid vault + local ISRC files for the rest.

## Next steps (new distributor)

1. Open `excavationpro_catalog.csv` in Excel/Google Sheets.
2. Filter `isrc` is not empty → these are your strongest re-delivery candidates.
3. Match audio masters on J: via `local_path` / `filename`.
4. While still able to open DistroKid vault, download masters + run the browser helper for UPC/release dates.
5. Email DistroKid support requesting a **full ISRC/UPC/release export** for artist Excavationpro (cite the Ania email).
6. Choose a new distributor (TuneCore, CD Baby, UnitedMasters, Amuse, etc.) and re-upload using the same ISRCs when allowed (reusing ISRC is normal for the same recording).

## Rebuild command

```bash
cd "I:\E Drive\lygo-protocol-stack"
python tools/music_catalog_recovery.py --out "I:\E Drive\lygo-protocol-stack\data\music_catalog"
# optional slower full J: scan:
python tools/music_catalog_recovery.py --full-j --out "I:\E Drive\lygo-protocol-stack\data\music_catalog"
```

## Legal / rights note

This registry is for **your own** catalog stewardship and re-distribution of **your** masters. Keep the DistroKid restriction email in your records.

Resonance: Δ9Φ963-MUSIC-CATALOG-RECOVERY
