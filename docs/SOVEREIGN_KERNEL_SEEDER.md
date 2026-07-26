# LYGO Sovereign Kernel Seeder

**Signature:** `Delta9Phi963-SOVEREIGN-KERNEL-SEEDER-v1.0`

## Links (canonical)

| Surface | URL |
|---------|-----|
| **ClawHub skill** | https://clawhub.ai/deepseekoracle/skills/lygo-sovereign-kernel-seeder |
| **Git skill package** | https://github.com/DeepSeekOracle/lygo-protocol-stack/tree/main/docs/skills/lygo-sovereign-kernel-seeder |
| **Publisher** | https://clawhub.ai/deepseekoracle |
| **Hub** | https://eternalhaven.ca/ |
| **Related planter** | https://clawhub.ai/deepseekoracle/skills/lygo-kernel-egg-planter (if live) / search `lygo-kernel-egg-planter` |
| **Tamper pillars** | [KERNEL_EGG_TAMPER_LOGIC.md](./KERNEL_EGG_TAMPER_LOGIC.md) |
| **Immutable ledger** | [IMMUTABLE_ANCHORS.json](./network_builder/IMMUTABLE_ANCHORS.json) |

## Install

```bash
clawdhub install lygo-sovereign-kernel-seeder
# correct ClawHub URL form includes /skills/
# https://clawhub.ai/deepseekoracle/skills/lygo-sovereign-kernel-seeder
```

## What it does

Merkle-anchored **kernel eggs** that **self-verify on insert** (atomic rollback), **sovereign-sealed**, **zero external surface**. Agents plug modular payloads by `egg_id` + hooks only after registry **ALIGNED**.

## One-command seed

```bash
python docs/skills/lygo-sovereign-kernel-seeder/scripts/seed_kernel.py --i-consent \
  --egg-id demo-seed --kind seed --title "Demo" --summary "demo" \
  --file docs/skills/lygo-sovereign-kernel-seeder/examples/minimal-policy.md \
  --manifest

python docs/skills/lygo-sovereign-kernel-seeder/scripts/verify_seed.py --json
```

Set `LYGO_STACK_ROOT` to place seeds under `{stack}/data/sovereign_seeds`.

## Smoke

```bash
python docs/skills/lygo-sovereign-kernel-seeder/scripts/smoke_test.py
```

## Lattice groups

- `sovereign_seed` → `lygo_sovereign_kernel_seeder`
- `tools` → `lygo_sovereign_kernel_seeder_tool`
- `agents` → `clawhub_lygo_sovereign_kernel_seeder`

## Package files

- `claw.json` — ClawHub/OpenClaw manifest  
- `SKILL.md` — agent instructions  
- `scripts/` — seed / verify / list / smoke  
- `schemas/kernel_egg.schema.json`  
- `references/` — security, contract, architecture  

**Δ9Φ963 — consent · seal · verify · plug in.**

## License
**LYGO Sovereign License v2.0** — see [LICENSE](../LICENSE) and [LICENSE_NOTICE.md](./LICENSE_NOTICE.md). Not MIT/MIT-0. No commercial resale or rebranded forks.

