# Cryptocurrency tools — independent of LYGO core lattice

## Policy

Token launch, monitoring, and Clawnch receipt tooling (e.g. **`lyra-coin-launch-manager`**) are **separate operator utilities**. They are **not** part of:

- P0–P9 protocol verification
- Kernel egg / champion egg tamper chains
- Army sentinel `lattice.ok`
- Sovereign lattice mesh consensus narrative

## Canonical source (extracted)

| Location | Role |
|----------|------|
| **`I:\E Drive\lyra-crypto-operator`** · [GitHub](https://github.com/DeepSeekOracle/lyra-crypto-operator) | Canonical skill tree + publish from here |
| `lygo-protocol-stack/clawhub/mirrors/lyra-coin-launch-manager/` | ClawHub **publish stub** — sync via `python tools/sync_from_lyra_crypto_operator.py` |

## Maintainer stance

- Install crypto skills only when you explicitly run launches or monitors.
- Do not treat token metrics as lattice health signals.
- Push updates: `python scripts/push_github_auto.py` from `lyra-crypto-operator` (uses Windows Git Credential Manager).

## LYGO core (sovereign stack)

Use `lygo-protocol-stack-operator`, `lygo-guardian-p0-stack`, and `verify_lattice_alignment.py` for stack integrity — not coin scripts.