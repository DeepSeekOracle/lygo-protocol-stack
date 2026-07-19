---
license: other
task_categories:
  - audio-to-audio
tags:
  - excavationpro
  - lygo
  - sovereign-music
  - streaming
pretty_name: Excavationpro Public Music Stream
size_categories:
  - 10K<n<100K
---

# Excavationpro public music stream (160 kbps)

**Owner / artist:** Justin Helmer · Excavationpro · Lightfather  
**Policy:** Own-work only. Public discovery streams (not DistroKid-dependent).  
**Lattice signature:** `Δ9Φ963-PUBLIC-MUSIC-STREAM-v1`

## Listen

- https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html  
- http://asiancoastline.com/ (custom domain music portal)

## Layout

| Path | Role |
|------|------|
| `stream/<sha256>.mp3` | Flat 160k streams (~first 10k − headroom) |
| `stream/<xx>/<sha256>.mp3` | Sharded overflow (`xx` = first 2 hex of sha) — HF **10k files/dir** limit |
| `public_stream_playlist.json` | Full index with per-track `stream_url` / `hf_path` |
| `play/play_counts.json` | Steward play lattice aggregate (optional client fallback) |

**Do not assume a single flat URL pattern for every track** — use `stream_url` from the playlist.

## Counts (2026-07-18)

- Public streams: **10,762**
- Bitrate: **160 kbps** MP3
- CAS vault masters (local steward): 10,762 unique SHA-256

## License / use

Own-work catalog for free listening and discovery. Commercial rights remain with the steward unless separately licensed. See listen portal footer + privacy.

## Stack

- GitHub: https://github.com/DeepSeekOracle/Excavationpro  
- Protocol: https://github.com/DeepSeekOracle/lygo-protocol-stack  
- Docs: `docs/SOVEREIGN_MUSIC_VAULT.md`, `docs/LATTICE_PUBLIC_HEALTH.md`
