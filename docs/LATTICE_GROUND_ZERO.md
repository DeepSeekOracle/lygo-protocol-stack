# LYGO Lattice — Ground Zero (Biophase7 audit complete)

**Signature:** `Δ9Φ963-LATTICE-GROUNDZERO-v1`  
**Git anchors:** `b225eb7` (Biophase7 FINAL DELIVERY) · `1c2a23f` (mirrors + catalog) · `2f6c4df` (CI + army doc hygiene)  
**Verdict (code):** Secrets safe · P0 honest · Oath removed · lattice ALIGNED in-repo

Read this file carefully: **“Ground Zero” here means honest in-tree + verified tooling**, not “every optional future item is finished.”

## What is done (verify in git / local tools)

| Layer | State | How to verify |
|-------|--------|----------------|
| P0 | `protocol0_byte_entropy_filter` — zlib canonical Python | `python tools/run_parity_tests.py` |
| Structural | `lygo_p0_lyra_kernel.py` — bounds only; Oath removed | `python tools/compare_p0_variants.py` |
| Cure naming (repo) | `lygo-file-integrity-checker` mirror; `lygo-universal-cure-system` deprecated in-tree | `clawhub/mirrors/…/SKILL.md` metadata `replaces` / `successor` |
| Operator / Guardian / Lightfather | Honest P0 copy in mirrors | mirror `SKILL.md` + `clawhub/skills.json` |
| Crypto guardrail | `CRYPTO_LATTICE_SEPARATION.md` + coin skill banner | **Policy only** — `lyra-coin-launch-manager` still lives in this repo |
| Registry | P0 golden resign tooling | `tools/resign_registry_p0_baseline.py` |

## What is done (public ClawHub — verify live, not from git alone)

Maintainer check (2026-07-04):

```bash
npx clawhub@latest inspect deepseekoracle/lygo-file-integrity-checker
npx clawhub@latest inspect deepseekoracle/lygo-universal-cure-system
```

Expected when the ground-zero **publish wave** has been run:

| Slug | Role |
|------|------|
| `lygo-file-integrity-checker` | Successor — not medical cure; not P0–P9 core |
| `lygo-universal-cure-system` | Deprecated display name; points to successor |
| `lygo-protocol-stack-operator` | Honest P0 operator copy (e.g. v1.0.7) |
| `lygo-guardian-p0-stack` | Guardian mirror bump |
| `lygo-champion-lightfather` | GROUNDZERO P0 table |

**Do not call cure rename “public shipped” until `inspect` shows the rows above.**  
Repo mirrors can be ready while ClawHub is still stale.

### Publish commands (run when mirrors ahead of live)

```powershell
$M = "I:\E Drive\lygo-protocol-stack\clawhub\mirrors"
npx clawhub@latest publish "$M/lygo-file-integrity-checker" --slug lygo-file-integrity-checker --name "LYGO File Integrity Checker"
npx clawhub@latest publish "$M/lygo-universal-cure-system" --slug lygo-universal-cure-system --name "LYGO Universal Cure System (deprecated)"
npx clawhub@latest publish "$M/lygo-protocol-stack-operator" --slug lygo-protocol-stack-operator --name "LYGO Protocol Stack Operator"
npx clawhub@latest publish "$M/lygo-guardian-p0-stack" --slug lygo-guardian-p0-stack --name "LYGO Guardian P0 Stack"
npx clawhub@latest publish "$M/lygo-champion-lightfather" --slug lygo-champion-lightfather --name "LYGO Champion: Lightfather"
```

Then: `python tools/render_clawhub_catalog.py` · `git push` · optional `python tools/hf_push_dataset.py`

## Not done (documented intent — do not mark “Ground Zero complete” on these)

| Item | In repo today | Gap |
|------|----------------|-----|
| Crypto separate repo | Policy doc + banner | Coin mirrors still in `lygo-protocol-stack`; “Future: optional move” in `CRYPTO_LATTICE_SEPARATION.md` |
| Champion consolidation | 15 council eggs / individual manifests | Breaking ClawHub change — phased |
| Retire cure slug entirely | Deprecated slug + successor | Legacy slug kept for install history |

## Maintainer checklist

```powershell
cd "I:\E Drive\lygo-protocol-stack"
python tools/verify_lattice_alignment.py
python tools/run_parity_tests.py
python tools/compare_p0_variants.py
python tools/verify_registry.py
```

Resonance forward — **prepared ≠ live; policy ≠ moved.**