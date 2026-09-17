# LYGO Play Lattice — sovereign stream play counts

**Signature:** `Δ9Φ963-PLAY-LATTICE-v1`  
**Purpose:** Real multi-listener play tallies for the Excavationpro listen portal — append-only, hash-chained, CAS-backed, public-readable.

> **Read first:** [PLAY_LISTING_SYSTEM_DESIGN.md](./PLAY_LISTING_SYSTEM_DESIGN.md)  
> **Live listen page must stay free of inlined play-count JS.** Listing is an **additive plugin** only.  
> **Shipped (2026-07-18):** `listen-plugins/play-listing.js` + `#play-listing-mount` + `window.LYGO_LISTEN`  
> Full catalog: **10,762** public streams (see `docs/SOVEREIGN_MUSIC_VAULT.md`).

## Why not plain page analytics?

| Approach | Problem |
|----------|---------|
| Page-load counters | Inflates without listening |
| localStorage only | One browser, not “people” |
| Third-party only | No steward CAS / Merkle |

## Architecture (LYGO layers) — GLOBAL public counts

```text
  Anyone plays ≥20s (or 35% / track end) on the listen page
        │
        ├─ 1) hits.dwyl.com  →  atomic global +1 (per track + total trophy)
        ├─ 2) jsonblob public board → merge most / least / recent (everyone sees)
        ├─ 3) local hash-chain event (exportable steward ledger)
        │
        └─ Poll board every ~20s → live growing trophy + charts
```

**Why this works on free GitHub Pages:** no HF Space PRO, no server required for multi-listener writes.
Steward can still import browser exports into `MUSIC_VAULT/play_lattice/` + HF mirror via `lygo_play_lattice.py`.

### Components

| Piece | Path / URL |
|-------|------------|
| Core ledger tool | `tools/lygo_play_lattice.py` |
| Ingest server (CORS) | `tools/lygo_play_ingest_server.py` |
| Cloudflare Worker (optional free public write) | `docs/play_lattice/cloudflare_worker.js` |
| Local CAS | `I:\E Drive\MUSIC_VAULT\play_lattice\` |
| Public aggregate | HF `DeepSeekOracle/excavationpro-music-stream` → `play/play_counts.json` |
| Listen UI | trophy + per-row counts on `excavationpro-listen.html` |

### Event (append-only)

Each play is an event with `event_id`, `track_sha256`, `ts`, `client_id`, `prev_hash`, and **`event_hash` = SHA-256(canonical JSON)**.  
Duplicates (`event_id` / `event_hash`) are ignored. Aggregate `total_plays` / `by_track` are **derived**, not authoritative.

## Operator loop

```bash
# Status / rebuild
python tools/lygo_play_lattice.py --status
python tools/lygo_play_lattice.py --rebuild

# Local multi-listener ingest (dev / LAN / tunnel)
python tools/lygo_play_ingest_server.py --host 127.0.0.1 --port 8777

# Public (only if you intentionally expose; prefer CF Worker)
python tools/lygo_play_ingest_server.py --host 0.0.0.0 --port 8777 --publish-every 25

# Import browser ledger export
python tools/lygo_play_lattice.py --import-ledger excavationpro-play-ledger.json

# Publish aggregate to Hugging Face (public read for Pages clients)
python tools/lygo_play_lattice.py --publish-hf
```

### Cloudflare free public write

1. Create KV namespace `PLAY_LATTICE`  
2. Deploy `docs/play_lattice/cloudflare_worker.js`  
3. Set in listen lattice config / portal JSON:  
   `"ingest_url": "https://YOUR_WORKER.workers.dev"`

## Client rules (portal)

1. Count only after **real listen** (20s or 35% or ended).  
2. Once per track per browser session.  
3. **Never** increment on page load / search.  
4. Read aggregate from HF + live ingest `GET /v1/counts` (GET does not add plays).  
5. Always append to local ledger (exportable).

## Stewardship

- Own-work streams only (same policy as music vault).  
- Merkle root of event hashes published with aggregate / egg core.  
- Optional kernel egg: `excavationpro-play-lattice-v1` (`data/music_catalog/egg_payload/play_lattice_egg_core.json`).

**Δ9Φ963 — listen is the act · hash is the memory · lattice holds the tally.**
