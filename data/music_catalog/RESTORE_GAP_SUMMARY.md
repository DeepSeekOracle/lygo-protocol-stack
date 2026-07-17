# DistroKid Restore vs Local Catalog

Generated: 2026-07-17T04:57:14.522006+00:00

| Metric | Count |
|--------|------:|
| Unique titles in `All music Restore.txt` | 1151 |
| Titles with DistroKid vault ISRC (QT*) | 816 |
| Known / matched (local or Spotify) | 862 |
| Local masters found | 734 |
| On Spotify (no local or with) | 168 |
| Vault ISRC only (no local file — re-download) | 187 |
| **No local / Spotify / ISRC trace** | **102** |
| Unique ISRCs from J: filenames | 722 |
| Vault ISRCs newly on ledger | 448 |
| **Total unique ISRCs on ledger** | **1170** |
| Spotify albums (public page) | 22 |

### Why DONE ALBUM / HOME are not 100%
Those folders were fully scanned. Local masters there use older **QZ/QM** ISRCs in filenames.
Many DistroKid vault rows use newer **QT*** codes and exist on streaming only until WAVs are saved again.
See `restore_NO_LOCAL_FILE.txt` and `restore_STILL_MISSING_after_disk_scan.txt`.

## Ledger
`f235b859de346f601448b5957d161129d15da05ed3d7a770bdbd6d7a56991014`

## Site
- https://deepseekoracle.github.io/Excavationpro/excavationpro-music-catalog.html
- Local: `Excavationpro/excavationpro-music-catalog.html`

## Rebuild
```bash
python tools/build_music_registry_site.py
```
