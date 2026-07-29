# Cross-system: Seeder ↔ Kernel Egg Planter

This seeder is **layer B** of the LYGO kernel egg system.  
Classic stack eggs are **layer A** (`lygo-kernel-egg-planter`).

See stack: `docs/KERNEL_EGG_SYSTEM_UNIFIED.md`

## Bridge commands

```bash
export LYGO_STACK_ROOT=/path/to/lygo-protocol-stack

# Unified verify (classic + sovereign)
python $LYGO_STACK_ROOT/tools/verify_all_kernel_layers.py --json

# Sovereign only
python scripts/verify_seed.py --root $LYGO_STACK_ROOT/data/sovereign_seeds --json

# Classic only (requires stack tools present)
python $LYGO_STACK_ROOT/tools/verify_kernel_eggs.py
```

## When seeder should hand off to planter

- User asks for P0 nano kernel, champion council, firmware drivers → **planter**  
- User asks for clawhub catalog plant / Turbo surfaces → **planter**  
- User asks for local policy/skill pin with no network → **seeder** (this skill)

## Shared agent contract

Consent · verify · quarantine · no secrets · no auto-publish.  
License: LYGO Sovereign License v2.0 for code; Music License v1.0 for music eggs.  
