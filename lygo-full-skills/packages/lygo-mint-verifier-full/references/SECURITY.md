# Security — lygo-mint-verifier v1.1.0

## Permissions

| Capability | Default |
|------------|---------|
| Network | **None** |
| Subprocess / shell | **None** (removed in 1.1.0) |
| Filesystem write | Ledgers under skill `state/` only with `--i-consent` |
| Publish | **None** — you paste Anchor Snippets yourself |

## Audit response

ClawHub security-audit previously flagged:

1. **subprocess module call** — fixed: in-process mint via `mint_cli.py`
2. **Undeclared permissions** — fixed: explicit metadata in SKILL.md + claw.json

## Operator rules

- Never put API keys / tokens in packs
- Review pack content before minting
- Prefer skill-local `state/`; use `--state-dir` only on paths you control
