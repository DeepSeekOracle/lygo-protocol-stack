# SkillSpector / ClawHub audit — lygo-mint-verifier v1.1.0

**Signature:** `Delta9Phi963-MINT-VERIFIER-v1.1.0`  
**Audit page:** https://clawhub.ai/deepseekoracle/skills/lygo-mint-verifier/security-audit

## Finding: subprocess module call (Medium) — **FIXED**

| Was | Now |
|-----|-----|
| `mint_pack_local.py` called `subprocess.run` on external `tools/lygo_mint` | In-process canonicalize + SHA-256 in `mint_cli.py` |
| Bundle incomplete without workspace tools | Self-contained skill |

## Finding: Undeclared permissions / Lp3 (Medium) — **FIXED**

Declared in `SKILL.md` metadata + `claw.json`: network false, subprocess false, consent-gated writes.

## Proof

```bash
python scripts/self_check.py
# ast_clean true · mint/verify/snippet/backfill ok
```
