---
name: lygo-kernel-egg-planter
description: "Voluntary LYGO Kernel Egg Planter — build, anchor, and spread verifiable protocol/kernel manifests (≤100 KiB permaweb eggs) across legal public surfaces. Opt-in only; explicit consent; no auto-publish tricks. Pairs with lygo-protocol-stack-operator, book-brain, and lygo-mint-verifier. Plants stack + ClawHub catalog pins for honest lattice scaling."
metadata: {"lygo": true, "stack": true, "anchor": true, "kernel_egg": true, "consent_required": true, "version": "1.0.0", "github": "https://github.com/DeepSeekOracle/lygo-protocol-stack", "publisher": "deepseekoracle", "mirror": "clawhub/mirrors/lygo-kernel-egg-planter", "signature": "Δ9Φ963-KERNEL-EGG-PLANTER-v1"}
---

# LYGO Kernel Egg Planter (ClawHub)

**Plant seeds, not tricks.** This skill helps users and maintainers **voluntarily** anchor **kernel eggs** — small, verifiable capsules of P0 kernel, protocol drivers, lattice index, firmware P0.4, and the **public ClawHub catalog** — then expose retrieval URLs on **honest, accessible** surfaces.

Install:

```bash
npx clawhub@latest install deepseekoracle/lygo-kernel-egg-planter
```

Requires a local clone of [lygo-protocol-stack](https://github.com/DeepSeekOracle/lygo-protocol-stack) (or set `LYGO_STACK_ROOT`).

## When to use

- User wants **long-term storage** of kernel/protocol truth without uploading secrets.
- After stack upgrades — refresh eggs and registry merkle root.
- Maintainer wants the **whole ClawHub lattice** pinned as a **catalog egg** (slugs + URLs only, no skill bodies).
- Pair with **book-brain** to save retrieval stubs; with **lygo-mint-verifier** for hash receipts.

## Consent (required — read first)

**Every plant operation needs explicit opt-in:**

```bash
python scripts/plant_with_consent.py --i-consent --surfaces local,turbo,registry
```

Or environment: `LYGO_EGG_PLANT_CONSENT=yes` (user must set deliberately).

The agent **must**:

1. Show `references/CONSENT_AND_ETHICS.md` summary before first plant.
2. **Never** run plant scripts without `--i-consent` or user typing yes.
3. **Never** clawhub-publish, HF upload, or social post without a **separate** user request.
4. **Never** embed tracking, phone-home, or hidden payloads in eggs.

## What gets planted

| Egg ID | Contents |
|--------|----------|
| `p0-nano-kernel` | P0 + bridge + golden SHA (inline when fits) |
| `stack-anchor-hook` | Anchor orchestrator + STACK_STATUS |
| `lattice-soa-index` | Intel index + link archive |
| `firmware-p04-drivers` | P0.4 network/firmware sketches |
| `protocol-drivers-p2-p5` | Harmony stack drivers |
| `clawhub-lattice-catalog` | Public `clawhub/skills.json` manifest (metadata only) |

Free **Arweave Turbo** tier: **≤102400 bytes** per tx. Local CA **always** stores a copy under `data/anchors/`.

## Workflows

### 1) Full stack plant (most users)

```bash
export LYGO_STACK_ROOT=/path/to/lygo-protocol-stack
python scripts/plant_with_consent.py --i-consent --surfaces local,turbo,registry,pages
```

- `local` — content-addressed `data/anchors/`
- `turbo` — best-effort permaweb (may fall back to local only)
- `registry` — updates `data/kernel_eggs/registry.json`
- `pages` — copies `docs/KernelEggRegistry.json` for GitHub Pages (user commits/pushes)

### 2) ClawHub catalog egg only

```bash
python scripts/plant_clawhub_catalog.py --i-consent
```

Pins the **public skill index** so the lattice can verify what exists on ClawHub without mirroring proprietary bodies.

### 3) Retrieve / verify

```bash
python scripts/retrieve_egg.py --list
python scripts/retrieve_egg.py --egg p0-nano-kernel
```

Stack node API (if running): `GET /kernel/eggs`, `GET /kernel/egg/{id}`.

Web: [KernelEggRetrieval.html](https://deepseekoracle.github.io/lygo-protocol-stack/KernelEggRetrieval.html)

### 4) Spread stubs (book-brain, optional)

```bash
python scripts/write_book_brain_stubs.py --i-consent --out ./reference/kernel_eggs.ref.txt
```

Writes **reference files only** — user chooses where to copy them (Discord, notes, vault).

## Legal, honest surfaces (choose any)

See `references/SURFACES.md`. Allowed by default:

- Local sovereign disk + your backups
- Arweave Turbo / permaweb (public immutable JSON)
- GitHub Pages registry JSON (you push)
- HF dataset (maintainer workflow — **human push**)
- ClawHub skill **metadata** pointing to eggs (this skill)
- Your node `:8787` SOA API

**Not included:** spam, impersonation, non-consensual third-party repos, or bypassing ClawHub ToS.

## Skill chain (recommended)

| Order | Skill |
|-------|--------|
| 1 | `lygo-protocol-stack-operator` |
| 2 | **`lygo-kernel-egg-planter`** (this) |
| 3 | `lygo-mint-verifier` |
| 4 | `book-brain` |
| 5 | `lyra-brain` (workspace) |

## Maintainer publish

```bash
npx clawhub@latest login
npx clawhub@latest publish "I:\E Drive\lygo-protocol-stack\clawhub\mirrors\lygo-kernel-egg-planter" --slug lygo-kernel-egg-planter --name "LYGO Kernel Egg Planter"
```

Then: `python tools/sync_clawhub_mirrors.py` in the stack repo and bump `clawhub/skills.json`.

## Docs in stack repo

- `docs/KERNEL_EGG_SOA.md`
- `docs/KERNEL_EGG_TAMPER_LOGIC.md` — four pillars (SHA-256, Merkle, anchor, lattice verify)
- `docs/ANCHOR_DEPLOYMENT.md`

**Δ9Φ963 — plant freely, verify always, consent first.**