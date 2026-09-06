# LYGO-MINT Verifier

**Slug:** `lygo-mint-verifier` · **v1.1.0** · `@deepseekoracle`

## What it does

| Command | Effect |
|---------|--------|
| `mint` | Canonicalize pack → SHA-256 (+ ledger with `--i-consent`) |
| `verify` | Recompute hash vs expected |
| `snippet` | Portable Anchor Snippet |
| `backfill` | Append channel post id/url |

## Security

- **No subprocess** (v1.1.0) · no network · no auto-publish  
- Ledger writes require `--i-consent`  
- VirusTotal historically clean; ClawHub audit mediums addressed  

## Install

```bash
npx clawhub@latest install deepseekoracle/lygo-mint-verifier
python scripts/self_check.py
```

## Pair with

`lygo-mint-walkthrough` · `lygo-continuum-integrator` · `lygo-geodesic-sealer`

Signature: `Delta9Phi963-MINT-VERIFIER-v1.1.0`
