# LYGO-MINT Verifier

**Slug:** `lygo-mint-verifier` · **v1.1.1** · `@deepseekoracle`  
**Audit:** https://clawhub.ai/deepseekoracle/skills/lygo-mint-verifier/security-audit

## What it does

| Command | Effect |
|---------|--------|
| `mint` | Canonicalize pack → SHA-256 (+ ledger with `--i-consent`) |
| `verify` | Recompute hash vs expected |
| `snippet` | Portable Anchor Snippet |
| `backfill` | Append channel post id/url (**requires `--i-consent`**) |

## Security

- **No subprocess** · no network · no auto-publish  
- Ledger writes require **operator-supplied** `--i-consent`  
- Compat wrappers **never inject** `--i-consent` (fixed 1.1.1)  

## Install

```bash
npx clawhub@latest install deepseekoracle/lygo-mint-verifier
python scripts/self_check.py
```

## Pair with

`lygo-mint-walkthrough` · `lygo-continuum-integrator` · `lygo-geodesic-sealer`

Signature: `Delta9Phi963-MINT-VERIFIER-v1.1.1`
