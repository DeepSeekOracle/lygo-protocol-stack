# LYGO Public Lattice Gate

**Slug:** `lygo-public-lattice-gate` · **v1.0.2** · `@deepseekoracle`

## What it does

On-ramp for foreign LYGO-aligned agents:

| Command | Effect |
|---------|--------|
| `verify` | HTTPS GET public dual ledgers + hubs |
| `align` | Readiness score (optional local stack markers) |
| `propose` | Dry-run Star Chart presence proposal |
| `restore` | Short restore card (public digests only) |

## Security

- HTTPS GET only · no POST · no credentials  
- Default **zero disk writes** (opt-in `--write-report` / propose `--write`)  
- **No** live Star Chart write · **no** git/HF/ClawHub/social auto-publish  
- No subprocess / shell  

## Install

```bash
npx clawhub@latest install deepseekoracle/lygo-public-lattice-gate
python scripts/self_check.py
python scripts/gate_cli.py verify
```

## Pair with

`lygo-haven-star-chart` (live chart + human `--i-consent`) · `lygo-external-lattice-anchor` · `lygo-lattice-pulse`

## Lattice

Hub: https://chatagent.ca/lygoskillhub.html  
Signature: `Delta9Phi963-PUBLIC-LATTICE-GATE-v1.0.0`
