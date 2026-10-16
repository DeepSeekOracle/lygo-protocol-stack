# LYGO TV

**Slug:** `lygo-tv` · **v1.3.1** · `@deepseekoracle`

## What it does

Pointer to the free online TV player, plus the drop-in player code. Agents print URLs and code; humans watch in
the browser, on our page or theirs.

| Command | Effect |
|---------|--------|
| `plain` | Directions to https://chatagent.ca/sources/ |
| `embed` | The three-line embed, what the visitor's browser then contacts, and the limits |
| `urls` | Canonical player / catalog / assets / terms |
| `bookmark` | Player URL to save |
| `donate` | PayPal / Patreon / Rumble |

## Embed

```html
<link rel="stylesheet" href="https://chatagent.ca/assets/lygo-tv-ninja.css?v=8">
<div data-lygo-tv></div>
<script src="https://chatagent.ca/assets/lygo-tv-ninja.js?v=8" defer></script>
```

Rumble room first · ~12,000 channels walked with Prev/Next · catalog from
https://chatagent.ca/sources/catalog.json (`Access-Control-Allow-Origin: *`) · MIT-0, keep the attribution.

## Security

- This folder's scripts: no network · no subprocess · no disk writes
- The embed: browser code that contacts chatagent.ca, cdn.jsdelivr.net (hls.js, SRI-pinned) and the channel's
  platform. Catalog URLs are https-checked and embed hosts pinned before anything is framed or played.
- No pirate proxy · no pay-TV decrypt · no XXX catalog
- Catalog is **RESOURCE** · dual ledgers stay **CANON**
- Audit: https://clawhub.ai/deepseekoracle/skills/lygo-tv/security-audit

## Install

```bash
npx clawhub@0.23.3 install deepseekoracle/lygo-tv@1.3.1
python scripts/self_check.py
python scripts/lygo_tv.py plain
```

## Lattice

Player: https://chatagent.ca/sources/  
Signature: `Delta9Phi963-LYGO-TV-v1.3.1`
