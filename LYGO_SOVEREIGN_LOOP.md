# LYGO Sovereign Loop — Desktop · USB · Lattice

**Signature:** D9Phi963-SOVEREIGN-LOOP-v1

Balanced triangle (no drift):

```
        [ Lattice verify ]
       lygo-protocol-stack
              /\
             /  \
            /    \
   [ Desktop ]----[ USB BUILDR ]
   lygo-claw      daemon :9630
   sovereign-loop  God-Mode vault
```

## One command (desktop)

```bat
lygo-claw\launchers\RUN_SOVEREIGN_LOOP.bat
```

Or: `lygo-claw sovereign-loop` (needs `LYGO_BUILDER_KEY_ROOT`, `LYGO_STACK_ROOT`, daemon optional).

## USB nightly

```bat
E:\LYGO_BUILDER_KEY\launchers\LYGO_Nightly_Brain_Loop.bat
```

## What runs

| Leg | Action |
|-----|--------|
| Desktop | `brain_init`/`brain_dream`, P0 gateway ping, `sovereign_loop_last_run.json` |
| USB | `usb-health`, optional `buildr-task verify_standalone`, `second_brain_loop` task |
| Lattice | `verify_lattice_alignment.py` on `LYGO_STACK_ROOT` |

Config on stick: `config/SOVEREIGN_LOOP.json`

Master log: [LYGO_USB_AND_CLAW_MASTER_WHITEPAPER.md](./LYGO_USB_AND_CLAW_MASTER_WHITEPAPER.md)

God-Mode reference: [LYGO_GODMODE_SECOND_BRAIN.md](./LYGO_GODMODE_SECOND_BRAIN.md)