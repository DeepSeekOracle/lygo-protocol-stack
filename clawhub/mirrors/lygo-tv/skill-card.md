# LYGO TV

**Slug:** `lygo-tv` · **v1.2.0** · `@deepseekoracle`

## What it does

Pointer to the free online TV player. Agents print URLs; humans watch in the browser.

| Command | Effect |
|---------|--------|
| `plain` | Directions to https://chatagent.ca/sources/ |
| `urls` | Canonical player / catalog / terms / disclaimer |
| `bookmark` | Player URL to save |
| `donate` | PayPal / Patreon / Rumble |

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
Signature: `Delta9Phi963-LYGO-TV-v1.2.0`
