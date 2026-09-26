# LYGO TV

**Slug:** `lygo-tv` · **v1.3.0** · `@deepseekoracle`

## What it does

Pointer to the free online TV player, plus the drop-in player code. Agents print URLs and code; humans
watch in the browser, on our page or on theirs.

| Command | Effect |
|---------|--------|
| `plain` | Directions to https://chatagent.ca/sources/ |
| `embed` | The three-line embed that runs the player on any site |
| `urls` | Canonical player / catalog / assets / terms |
| `bookmark` | Player URL to save |
| `donate` | PayPal / Patreon / Rumble |

## Embed

```html
<link rel="stylesheet" href="https://chatagent.ca/assets/lygo-tv-ninja.css?v=7">
<div data-lygo-tv></div>
<script src="https://chatagent.ca/assets/lygo-tv-ninja.js?v=7" defer></script>
```

Rumble room first · ~12,000 channels walked with Prev/Next · feed from
https://chatagent.ca/sources/catalog.json (`Access-Control-Allow-Origin: *`) · MIT-0, keep the attribution.

## Security

- No network · no subprocess · no disk writes
- No pirate proxy · no pay-TV decrypt · no XXX catalog
- Catalog is **RESOURCE** · dual ledgers stay **CANON**

## Install

```bash
npx clawhub@latest install deepseekoracle/lygo-tv
python scripts/self_check.py
python scripts/lygo_tv.py plain
```

## Lattice

Player: https://chatagent.ca/sources/  
Signature: `Delta9Phi963-LYGO-TV-v1.3.0`
