# DistroKid Restore vs Local Catalog

Generated: 2026-07-17T04:34:21.827576+00:00

| Metric | Count |
|--------|------:|
| Unique titles in `All music Restore.txt` | 761 |
| Titles with DistroKid vault ISRC (QT*) | 392 |
| Known / matched (local or Spotify) | 475 |
| Local masters found | 347 |
| On Spotify (no local or with) | 160 |
| Vault ISRC only (no local file — re-download) | 179 |
| **No local / Spotify / ISRC trace** | **107** |
| Unique ISRCs from J: filenames | 722 |
| Vault ISRCs newly on ledger | 424 |
| **Total unique ISRCs on ledger** | **1146** |
| Spotify albums (public page) | 22 |

### Why DONE ALBUM / HOME are not 100%
Those folders were fully scanned. Local masters there use older **QZ/QM** ISRCs in filenames.
Many DistroKid vault rows use newer **QT*** codes and exist on streaming only until WAVs are saved again.
See `restore_NO_LOCAL_FILE.txt` and `restore_STILL_MISSING_after_disk_scan.txt`.

## Ledger
`6f451d1560977955adbf06f9ffd2939d6e337866654208f3c73d32d874240700`

## Site
- https://deepseekoracle.github.io/Excavationpro/excavationpro-music-catalog.html
- Local: `Excavationpro/excavationpro-music-catalog.html`

## Rebuild
```bash
python tools/build_music_registry_site.py
```
