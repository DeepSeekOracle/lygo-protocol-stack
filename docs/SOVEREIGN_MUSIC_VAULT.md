# Sovereign Music Vault — Excavationpro

**Goal:** Keep *your actual masters* findable and playable even if DistroKid / Spotify / YouTube Music take them down.

**Signature:** `Δ9Φ963-SOVEREIGN-MUSIC-VAULT-v1`

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
