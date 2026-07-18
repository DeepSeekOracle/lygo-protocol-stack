# DistroKid Restore vs Local Catalog

Generated: 2026-07-18T02:56:11.099624+00:00

| Metric | Count |
|--------|------:|
| Unique titles in `All music Restore.txt` | 1151 |
| Titles with DistroKid vault ISRC (QT*) | 816 |
| Known / matched (local or Spotify) | 1075 |
| Local masters found | 587 |
| On Spotify (no local or with) | 1067 |
| Vault ISRC only (no local file — re-download) | 1 |
| **No local / Spotify / ISRC trace** | **75** |
| Unique ISRCs from J: filenames | 722 |
| Vault ISRCs newly on ledger | 448 |
| **Total unique ISRCs on ledger** | **1170** |
| Spotify albums (public page) | 407 |

### Why DONE ALBUM / HOME are not 100%
Those folders were fully scanned. Local masters there use older **QZ/QM** ISRCs in filenames.
Many DistroKid vault rows use newer **QT*** codes and exist on streaming only until WAVs are saved again.
See `restore_NO_LOCAL_FILE.txt` and `restore_STILL_MISSING_after_disk_scan.txt`.

## Ledger
`e451c37e706377bdf40b0e11c6247a5ece1093e808b225e421c6dc5cfbb7fa6a`

## Site
- https://deepseekoracle.github.io/Excavationpro/excavationpro-music-catalog.html
- Local: `Excavationpro/excavationpro-music-catalog.html`

## Rebuild
```bash
python tools/build_music_registry_site.py
```
