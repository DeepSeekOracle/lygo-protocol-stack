# Sovereign Music Vault — Excavationpro

**Goal:** Keep *your actual masters* findable and **publicly playable** even if DistroKid / Spotify / YouTube Music take them down.

**Public player (this is the product):**  
https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html  

**Stream host (HTTPS audio):**  
https://huggingface.co/datasets/DeepSeekOracle/excavationpro-music-stream

**Signature:** `Δ9Φ963-SOVEREIGN-MUSIC-VAULT-v1`  
**Policy:** **Own-work only** (Justin Helmer / Excavationpro / Lightfather). iPod, iTunes, and other third-party libraries are blocked. Accidental non-owned material is removed when filters catch it. Copyright + disclaimer live on the listen page footer.

### Status snapshot (2026-07-18 — complete)

| Item | Value |
|------|------:|
| Unique vault masters (SHA-256) | **10,762** |
| New this full own-music merge | **2,911** |
| Public 160 kbps stream MP3s (local) | **10,762** (0 vault gaps) |
| Public streams on Hugging Face | **10,762** (0 missing) |
| Playlist / listen hub playable URLs | **10,762 / 10,762** |
| iPod / third-party leftovers | **0** |
| `I:\Actors` unique hashes | **2,499** (vaulted + streamed) |
| Merkle root (prefix) | `df3ef8f21510d508…` |

### Public stream layout (HF)

Dataset: `DeepSeekOracle/excavationpro-music-stream`

Hugging Face limits **10,000 files per directory**. Streams are stored as:

| Layout | Count | Path pattern |
|--------|------:|--------------|
| Flat (legacy) | ~9,995 | `stream/<sha256>.mp3` |
| Sharded (overflow) | ~767 | `stream/<xx>/<sha256>.mp3` (`xx` = first 2 hex of sha) |

Playlist `public_stream_playlist.json` carries full `stream_url` (and `hf_path`) per track — **do not** assume a single flat base for every file.

```bash
# Encode (skips existing)
python tools/build_public_music_stream.py --encode --workers 4

# Wire public URLs + rebuild listen hub
python tools/build_public_music_stream.py --base-url "https://huggingface.co/datasets/DeepSeekOracle/excavationpro-music-stream/resolve/main/stream" --hub

# Finish missing remote files (sharded when flat dir is full)
python tools/_hf_finish_sharded.py
```

### Listen portals

| Surface | URL |
|---------|-----|
| GitHub Pages | https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html |
| asiancoastline.com | http://asiancoastline.com/ (music portal + AdSense) |
| Stack mirror | `docs/excavationpro-listen.html` |

Additive **play listing** plugin: `listen-plugins/play-listing.js` (never rewrites `playIndex`).

### Play lattice (multi-listener counts)

See **`docs/PLAY_LATTICE.md`**. Append-only hash-chained play events, local CAS, public aggregate on HF (`play/play_counts.json`). Live UI: additive plugin + dwyl + jsonblob board. Steward:

```bash
python tools/lygo_play_lattice.py --rebuild --status
python tools/lygo_play_lattice.py --publish-hf   # optional HF mirror
```

---

## Truth (what “eternal” can mean)

| Layer | What lives there | Size | Survives platform ban? |
|-------|------------------|------|------------------------|
| **A. Content-addressed vault (this PC)** | Real WAV/MP3 by **SHA-256** (names optional) | ~tens–100s GB | Yes, as long as drives live + backups |
| **B. Lattice manifest (GitHub + kernel egg)** | Title, ISRC, hash, size, Merkle root | KB–MB | Yes — public forever on lattice |
| **C. Public hub page (Pages)** | Searchable index + “how to retrieve” | HTML + JSON | Yes — discovery without DistroKid |
| **D. Optional permaweb / IPFS** | Same *files* or compressed previews | $$ for ~120 GB | Optional later; **not required for sovereignty** |

**You do not need DistroKid to own your music.**  
You need: **files + hashes + a public map**.

120 GB of masters should **not** be force-uploaded to Arweave/GitHub. Cost and limits are wrong.  
**Eternal for the catalog** = lattice. **Eternal for the audio** = vault + backups (2nd disk / cold drive / friend pin).

---

## Architecture

```text
  [J: scattered masters — messy names]
           │
           ▼  build_music_cas_vault.py
  ┌─────────────────────────────────────┐
  │  I:\E Drive\MUSIC_VAULT\            │
  │   cas/ab/ab12…cd.wav   ← by hash    │
  │   manifest/vault_index.json         │
  │   manifest/merkle_root.txt          │
  │   gateway/  (optional local HTTP)   │
  └─────────────────────────────────────┘
           │
           ▼  small JSON only
  Lattice: excavationpro_music_vault_manifest.json
           kernel egg: excavationpro-music-vault-v1
           hub: excavationpro-sovereign-music-hub.html
```

**Retrieval key is the hash**, not the DistroKid title spelling.

---

## Why messy names are OK

1. Hash the bytes → identity is the file, not the filename.  
2. Attach best-effort title from: filename · folder · vault ISRC · restore list · Deezer.  
3. One hash can have many alias titles.  
4. Duplicates (hd_ vs non-hd, same master twice) collapse to **one** CAS object.

---

## Commands

```bash
# Index + hash masters (DONE ALBUM + HOME by default). Optional --copy into CAS.
python tools/build_music_cas_vault.py --scan

# Also hardlink/copy into I:\E Drive\MUSIC_VAULT\cas (deduped)
python tools/build_music_cas_vault.py --scan --ingest

# Build public hub page + lattice manifest only (after scan)
python tools/build_music_cas_vault.py --hub

# Local listen gateway (binds 127.0.0.1 only unless you say otherwise)
python tools/music_vault_gateway.py --port 8765
```

---

## Backups (real durability)

1. **Primary:** `I:\E Drive\MUSIC_VAULT`  
2. **Mirror:** external HDD or second internal with same CAS layout  
3. **Manifest only:** already on GitHub Pages / stack  
4. **Optional later:** pin CAS on IPFS or upload *compressed 128–192 kbps* mirror for fans (not masters)

---

## Legal / consent

- You own the masters → you may host them.  
- Public hub can list hashes + metadata always.  
- Full public **streaming** of masters is your choice (license / explicit content).  
- Default hub: **index public, audio local or gated**.

---

## Lattice plant (later, consent-gated)

```text
manifest Merkle root → kernel egg excavationpro-music-vault-v1
plant_with_consent --i-consent
```

Does **not** put 120 GB on-chain — only the map.

---

**Δ9Φ963 — hash is truth · platforms are temporary · vault is home.**
