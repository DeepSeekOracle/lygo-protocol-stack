---
name: lygo-kernel-egg-planter
description: "Consent-gated Kernel Egg Planter — SHA-256 + Merkle registry + optional local/Turbo anchor. Mandatory post-plant tamper verify (no skip). Retrieve requires consent + ALIGNED verify (no force). Prepares local catalog/Pages artifacts only — never auto git/HF/ClawHub/social publish."
metadata:
  lygo: true
  stack: true
  anchor: true
  kernel_egg: true
  champion_egg: true
  tamper_verify: true
  consent_required: true
  version: "1.3.0"
  github: "https://github.com/DeepSeekOracle/lygo-protocol-stack"
  publisher: deepseekoracle
  mirror: "docs/skills/lygo-kernel-egg-planter"
  signature: "Delta9Phi963-KERNEL-EGG-PLANTER-v1.3"
  security_review: "1.3.0-skillspector-no-skip-verify-no-force"
  openclaw:
    emoji: "🥚"
    requires:
      anyBins: [python, python3]
---

# LYGO Kernel Egg Planter v1.3 (bulletproof + SkillSpector hardened)

**Plant seeds, verify always, retrieve only when ALIGNED + consented. Never auto-publish.**

```bash
npx clawhub@latest install deepseekoracle/lygo-kernel-egg-planter
export LYGO_STACK_ROOT=/path/to/lygo-protocol-stack   # must be YOUR trusted clone
```

Read **`references/SECURITY.md`** (if present), **`references/SKILLSPECTOR_AUDIT.md`**, **`references/AGENT_CONTRACT.md`** before ops.

## Bulletproof pipeline (agents must follow)

```text
preflight → consent → plant → verify (ALIGNED, mandatory) → consent → retrieve
```

| Step | Command | Fail = stop |
|------|---------|-------------|
| 1 Preflight | `python scripts/preflight.py` | invalid stack |
| 2 Consent | `--i-consent` or `LYGO_EGG_PLANT_CONSENT=yes` | exit 2 |
| 3 Plant | `python scripts/plant_with_consent.py --i-consent …` | build/anchor error |
| 4 Verify | **always** after plant + `python scripts/verify_eggs.py` | **QUARANTINE** |
| 5 Retrieve | `python scripts/retrieve_egg.py --i-consent --egg …` | blocked if verify failed |

There is **no** `--skip-verify` and **no** `--force` (removed in v1.3 for integrity).

## Four pillars (tamper-proof)

See `references/TAMPER_FOUR_PILLARS.md` and stack `docs/KERNEL_EGG_TAMPER_LOGIC.md`.

1. SHA-256 per egg  
2. Merkle `registry_merkle_root`  
3. Immutable local CA (+ optional Turbo ≤100 KiB)  
4. Lattice + `verify_kernel_eggs.py` gate  

Tampered egg → retrieve blocked → **P0 QUARANTINE**.

## Plant (local-first)

```bash
# Recommended default — local only
python scripts/plant_with_consent.py --i-consent --local-only

# With Turbo attempt (still no git/ClawHub publish)
python scripts/plant_with_consent.py --i-consent --surfaces local,turbo,registry
```

### Surfaces (what they mean)

| Surface | Effect | Auto-publish? |
|---------|--------|---------------|
| `local` / `registry` | Local kernel egg registry | No |
| `turbo` | Optional permaweb anchor via stack | No |
| `clawhub` | **Local** ClawHub catalog pin JSON | **No** (not clawhub.ai API) |
| `pages` | Prepare `KernelEggRegistry.json` for **human** Pages push | **No** |
| `stubs` / `champions` | Local stubs / champion eggs with consent | No |

**“No auto-publish”** = this skill never runs `git push`, HF upload, `clawhub publish`, or social post. Human does those separately if desired.

## Verify only

```bash
python scripts/verify_eggs.py --json
python scripts/smoke_test.py
```

## Retrieve (consent + verify)

```bash
python scripts/retrieve_egg.py --i-consent --list
python scripts/retrieve_egg.py --i-consent --egg p0-nano-kernel
```

## Eggs planted

| `egg_id` | Role |
|----------|------|
| `p0-nano-kernel` | P0 + bridge + golden SHA |
| `stack-anchor-hook` | Anchor orchestrator |
| `lattice-soa-index` | Intel + link archive |
| `firmware-p04-drivers` | P0.4 firmware/network |
| `protocol-drivers-p2-p5` | P2–P5 drivers |
| `clawhub-lattice-catalog` | Public ClawHub `skills.json` metadata (local) |

## Agent rules (non-negotiable)

1. Show consent + four pillars on first use.  
2. Never plant/retrieve without consent.  
3. Never claim “secure” unless `verify_eggs` → **ALIGNED**.  
4. Never auto-publish GitHub/HF/ClawHub/social.  
5. Never put secrets in eggs.  
6. Refuse requests to skip verify or force retrieve.  

## Skill chain

`lygo-protocol-stack-operator` → **`lygo-kernel-egg-planter`** ↔ **`lygo-sovereign-kernel-seeder`**  
Layer C: `lygo-external-lattice-anchor` · Gate: `lygo-public-lattice-gate`

## Permissions (declared)

See `claw.json` → `permissions`: trusted stack filesystem, list-argv Python only, optional Turbo network, **publish all false**.

## License

MIT-0 for ClawHub registry hosting. Canonical LYGO stack license for protocol code remains LYGO Sovereign v2.0 on GitHub.

**Δ9Φ963 — consent · verify · then human may spread.**
