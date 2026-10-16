# Ground Zero reference — what it actually means

**Signature:** `Δ9Φ963-GROUND-ZERO-REFERENCE-v1`  
**Filename note:** This doc was `LATTICE_GROUND_ZERO.md`; renamed so the **title matches the content** (status reference, not “everything finished”).

**Git anchors:** `b225eb7` · `1c2a23f` · `2f6c4df` · `c1d56c0`  
**Verdict (code):** Secrets safe · P0 honest · Oath removed · lattice ALIGNED in-repo

**“Ground Zero”** = honest in-tree baseline + verified tooling. Optional roadmap items have their own docs.

## Done (verify in git / local tools)

| Layer | State | How to verify |
|-------|--------|----------------|
| P0 | `protocol0_byte_entropy_filter` — zlib canonical | `python tools/run_parity_tests.py` |
| Structural | Oath removed; bounds only | `python tools/compare_p0_variants.py` |
| Cure naming (repo) | file-integrity-checker + deprecated cure mirror | `clawhub/mirrors/…/SKILL.md` |
| Crypto extraction | Canonical **`I:\E Drive\lyra-crypto-operator`** + stack sync tool | `docs/CRYPTO_LATTICE_SEPARATION.md` |
| Champion template | `clawhub/templates/champion-pack/` + `sync_champion_pack_template.py` | `docs/CHAMPION_CONSOLIDATION.md` |
| Registry / eggs | Kernel + champion registries in `data/` + `docs/*Registry.json` | `verify_kernel_eggs.py` / `verify_champion_eggs.py` |

## Done (ClawHub — verify live with `inspect`, not git)

```bash
npx clawhub@latest inspect deepseekoracle/lygo-file-integrity-checker
npx clawhub@latest inspect deepseekoracle/lygo-universal-cure-system
```

Publish when mirrors ahead of live — see `clawhub/mirrors/` and `python tools/render_clawhub_catalog.py`.

## Not done / external verify

| Item | Status |
|------|--------|
| HF dataset tip | Maintainer-reported; verify on huggingface.co if needed |
| Crypto repo on GitHub | Local `lyra-crypto-operator` ready; `git push` to `DeepSeekOracle/lyra-crypto-operator` when remote exists |
| Single ClawHub champion slug | Deferred — template sync only |
| Retire cure slug entirely | Deprecated + successor; legacy slug kept |

## Maintainer checklist

```powershell
cd "I:\E Drive\lygo-protocol-stack"
python tools/verify_lattice_alignment.py
python tools/run_parity_tests.py
python tools/sync_champion_pack_template.py
python tools/sync_from_lyra_crypto_operator.py
```

Resonance forward — **prepared ≠ live; policy ≠ moved; filename ≠ claim.**