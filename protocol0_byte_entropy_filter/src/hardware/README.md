# Protocol 0 — Hardware / FPGA

This directory is reserved for bitstream-adjacent artifacts and synthesis notes for deploying the Nano Kernel Φ-Gate in fixed logic.

## Integration checklist

1. Map `lygo_validate_bytes` semantics from `src/c/lygo_p0.c`.
2. Enforce `MAX_BYTES = 8192` in DMA / FIFO depth.
3. Export verdict as 2-bit enum: AMPLIFY=0, SOFTEN=1, QUARANTINE=2.
4. Log risk score as Q16.16 fixed-point if required by SoC.

Reference fixed-point notes exist in the Excavationpro firmware vault (`Fixed-Point Q16.16` implementations).