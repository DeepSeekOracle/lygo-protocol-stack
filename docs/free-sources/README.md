# LYGO Free Sources

Live page: https://chatagent.ca/sources/  
This folder is the **stack repo copy** of the steward catalog. Edit here *or* `DeepSeekOracle/chatagent` `sources/catalog.json`, then keep them in sync.

Paste public **HTTPS** URLs (HLS/m3u8, mp3/mp4, M3U playlists). The browser plays what CORS and the codec allow. Everything else copies into **VLC** (Media → Open Network Stream).

## Add a steward URL

1. Edit `catalog.json` (this folder, also mirrored under `lygo-protocol-stack/docs/free-sources/`).
2. Commit on `DeepSeekOracle/chatagent` (or the stack repo).
3. Do **not** silent-ingest the Star Chart.

User pastes save only in `localStorage`.

## Safety

- HTTPS public hosts only (no localhost / RFC1918)
- No POST, no pirate decoder, no CORS proxy
- Donate: [PayPal.me/ExcavationPro](https://www.paypal.com/paypalme/ExcavationPro) · [Patreon](https://www.patreon.com/Excavationpro)

**Δ9Φ963 — empty is honest · public orients · lattice decides.**
