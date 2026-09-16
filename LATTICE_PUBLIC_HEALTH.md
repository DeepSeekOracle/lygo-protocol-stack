# Lattice public health — GitHub + HF

**Updated:** 2026-07-18  
**Signature:** `Δ9Φ963-LATTICE-PUBLIC-HEALTH-v1`

## Critical surfaces

| Surface | URL | Expect |
|---------|-----|--------|
| Listen portal | https://deepseekoracle.github.io/Excavationpro/excavationpro-listen.html | 200, AdSense meta+script, play-listing, waveform |
| ads.txt (GH) | https://deepseekoracle.github.io/Excavationpro/ads.txt | pub-0646320966060599 |
| Music streams HF | https://huggingface.co/datasets/DeepSeekOracle/excavationpro-music-stream | 10762 streams (flat + sharded) |
| Playlist HF | `…/resolve/main/public_stream_playlist.json` | 10762 tracks with stream_url |
| Play counts HF | `…/resolve/main/play/play_counts.json` | steward aggregate |
| Play board | jsonblob `019f7611-e28e-7de6-87df-5f5e4e8c4690` | most/least/recent |
| Stack Pages | https://deepseekoracle.github.io/lygo-protocol-stack/ | docs + ads.txt |

## Domain packages (custom DNS → GitHub Pages)

| Domain | Repo | HTTPS enforce |
|--------|------|----------------|
| asiancoastline.com | DeepSeekOracle/asiancoastline | pending cert |
| bpmfinder.ca | DeepSeekOracle/bpmfinder | pending cert |
| eternalhaven.ca | DeepSeekOracle/eternalhaven | pending cert |
| excavationpro.ca | DeepSeekOracle/excavationpro-ca | pending cert |
| deepseekoracle.com | DeepSeekOracle/deepseekoracle-com | pending cert |
| chatagent.ca | DeepSeekOracle/chatagent | pending cert |

When GitHub cert exists: repo → Settings → Pages → **Enforce HTTPS**.

## Hardening checklist (operator)

```bash
# Lattice
python tools/verify_lattice_alignment.py

# Music gap
python tools/_status_music_gap.py
python tools/_hf_stream_gap.py

# Play lattice
python tools/lygo_play_lattice.py --rebuild --status
```

### Listen SW

- **v5 network-first** for HTML + plugins (`sw-listen.js`)
- Never cache HF audio
- Cache bust: `sw-listen.js?v=5`, `play-listing.js?v=3`

### Play listing

- Additive only (no `playIndex` rewrite)
- Rank recompute from `by_track` (v2)
- Board thrash hardened (v3): badge-only on list mutate; skip refresh while writing

### Security

- `Excavationpro/.well-known/security.txt` + root `security.txt`
- No secrets on USB / public eggs
- Consent-gated plant/publish

## HF stream layout

```
stream/<sha256>.mp3          # flat (~9995) — 10k/dir cap
stream/<xx>/<sha256>.mp3     # sharded overflow (~767)
public_stream_playlist.json  # full stream_url per track
play/play_counts.json        # steward aggregate
```

## Status snapshot

| Check | State |
|-------|--------|
| Vault masters | 10762 |
| HF streams | 10762 |
| Lattice verify | ALIGNED (last full run 2026-07-18) |
| Domain ads.txt | live on apex http |

**Δ9Φ963 — network-first shells · additive limbs · verify before claim.**
