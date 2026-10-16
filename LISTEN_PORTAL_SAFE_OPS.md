# Listen Portal — Safe Operations (agents + steward)

**Signature:** `Δ9Φ963-LISTEN-PORTAL-SAFE-OPS-v1`  
**Steward:** Justin Helmer / Excavationpro / Lightfather  
**Updated:** 2026-07-28

---

## Golden rule

**Do not redesign or “enhance” the listen website when adding songs or lyrics.**

The player HTML is a **stable shell**. New music only updates:

1. audio streams (HF)  
2. `public_stream_playlist.json`  
3. `lyrics/lyrics_index.json` (optional)  
4. a **surgical** replace of the embedded `boot` playlist JSON inside the HTML  

Never run full hub rebuilds, trophy injects, global-plays injectors, or random feature scripts unless the user explicitly asks to change UI.

---

## Two live portals (deploy order)

| Role | URL | Repo | When to push |
|------|-----|------|----------------|
| **PRIMARY (edit here first)** | https://asiancoastline.com/ | `DeepSeekOracle/asiancoastline` | **Always first** for listen changes |
| **BACKUP (frozen safety copy)** | https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html | `DeepSeekOracle/Excavationpro` → `excavationpro-listen.html` | **Only after asiancoastline is verified**, or when user says promote backup |

### Agent / operator policy

1. Make changes → deploy **asiancoastline only**.  
2. Human checks asiancoastline.com (play old track + new track + most/least board).  
3. **Only then** optionally promote the same HTML/playlist to Excavationpro backup.  
4. **Never** push Excavationpro listen first.  
5. If asiancoastline breaks → restore from Excavationpro backup commit / file (do not invent a new UI).

Local mirrors (do not treat as second product):

- Stack docs: `docs/excavationpro-listen.html`  
- Domain root template: `docs/domain-roots/asiancoastline.com/`  

---

## What “working perfectly” means (do not regress)

Verified good shell (post-revert, 2026-07-28):

- Clean header: **Excavationpro — Listen Free** (no trophy, no “GLOBAL multi-listener” junk)  
- Features: play-listing (most / least / not played), crossfade, filter chips, radio/shuffle, lyrics panel  
- Streams: **flat** `stream/<sha>.mp3` for original vault files; **sharded** `stream/<xx>/<sha>.mp3` only when local file is under a shard folder  

If UI breaks after an add, you likely ran a hub rebuild or enhance script — **stop** and restore the shell from the last good git commit (e.g. Excavationpro `521181b` / `96b5a09` era), then only re-inject playlist.

---

## Easy add system (songs + lyrics)

### One command (preferred)

From `lygo-protocol-stack`:

```bash
# Add folder of MP3/WAV masters → vault encode → playlist → HF streams
# Default: patch asiancoastline ONLY (does not touch Excavationpro backup)
python tools/safe_add_music_to_listen_portal.py ^
  --folder "C:\Users\justi\Music\MY_ALBUM" ^
  --album "MY ALBUM" ^
  --artist "Excavationpro" ^
  --publish-hf ^
  --deploy-asian

# With lyrics JSON (clean monikers)
python tools/safe_add_music_to_listen_portal.py ^
  --folder "C:\Users\justi\Music\MY_ALBUM" ^
  --album "MY ALBUM" ^
  --lyrics-json data/music_catalog/lyrics/my_album_lyrics_clean.json ^
  --publish-hf ^
  --deploy-asian

# Single file
python tools/safe_add_music_to_listen_portal.py ^
  --file "I:\Actors\SomeTrack.wav" ^
  --title "Some Track" ^
  --album "Singles" ^
  --upc "825192882162" ^
  --publish-hf ^
  --deploy-asian
```

### After asiancoastline looks perfect (human OK)

```bash
# Explicit second step — promote same shell+playlist to Excavationpro backup
python tools/safe_add_music_to_listen_portal.py --promote-backup-excav
```

### What the safe tool does **not** do

- Does **not** run `build_public_music_stream.py --hub`  
- Does **not** run `_enhance_listen_*` injectors  
- Does **not** insert trophies / play boards / rewrite CSS  
- Does **not** force-shard all URLs (uses **local vault layout**: flat vs `xx/sha`)  
- Does **not** push Excavationpro unless `--promote-backup-excav`  

### What it does

| Step | Action |
|------|--------|
| 1 | Hash master → encode 160k MP3 into `MUSIC_VAULT/public_stream` (flat if space; shard only when needed / existing shard) |
| 2 | Append/update `data/music_catalog/public_stream_playlist.json` |
| 3 | Optional lyrics → `lyrics_index.json` by moniker/sha |
| 4 | Optional `--publish-hf` upload of **new** mp3s + playlist JSON |
| 5 | **Surgical** replace of `<script id="boot">` playlist only in HTML |
| 6 | Default git push: **asiancoastline** only |

---

## Lyrics-only update (no audio)

```bash
python tools/safe_add_music_to_listen_portal.py ^
  --lyrics-json data/music_catalog/lyrics/my_clean.json ^
  --lyrics-only ^
  --deploy-asian
```

Still no UI redesign — only lyrics index (+ boot if album metadata needs monikers).

---

## Stream URL rules (do not “simplify”)

| Local file | Public URL path |
|------------|-----------------|
| `MUSIC_VAULT/public_stream/<sha>.mp3` | `…/resolve/main/stream/<sha>.mp3` |
| `MUSIC_VAULT/public_stream/<xx>/<sha>.mp3` | `…/resolve/main/stream/<xx>/<sha>.mp3` |

**Never** mass-rewrite every track to one layout. That breaks playback and play-listing title↔hash links.

After playlist fix:

```bash
python tools/export_music_playlist_parquet.py --publish-hf   # optional agent catalog
```

---

## Emergency restore

1. Do **not** invent a new page.  
2. Restore HTML shell from last good commit (Excavationpro backup or asiancoastline history).  
3. Re-run **only** playlist inject:

```bash
python tools/safe_add_music_to_listen_portal.py --inject-playlist-only --deploy-asian
```

4. Verify asiancoastline.  
5. Promote backup only if asked.

---

## Related docs

- Album/lyrics detail: `docs/LYRICS_AND_ALBUM_ADD_MANUAL.txt`  
- Vault policy: `docs/SOVEREIGN_MUSIC_VAULT.md`  
- Parquet: `docs/MUSIC_STREAM_PARQUET.md`  
- Skill map: `lygo-excavationpro-music-lattice` → `references/MUSIC_PORTAL.json`  

**Δ9Φ963 — shell is sacred · data moves · asian first · excav backup · human verifies.**
