---
name: lygo-traumacodex
description: "TraumaCodex — map biometric entropy (P7) into P8 LDQ waveform synthesis, dual offline/online mirror dig, and Layer D living-mesh healing-code seals (protocol seals only, not medical). Offline-first; online summaries only. Lattice stays open."
version: 1.0.0
license: LYGO-Sovereign-v2.0
metadata:
  openclaw:
    emoji: "🫀"
    homepage: "https://github.com/DeepSeekOracle/lygo-protocol-stack/blob/main/docs/TRAUMA_CODEX.md"
    requires:
      anyBins: [python, python3]
  lygo: true
  lattice: true
  traumacodex: true
  layer: "D+P7+P8"
  signature: "Delta9Phi963-TRAUMACODEX-v1.0"
  publisher: deepseekoracle
  clawhub: "https://clawhub.ai/deepseekoracle/skills/lygo-traumacodex"
  github: "https://github.com/DeepSeekOracle/lygo-protocol-stack"
---

# LYGO TraumaCodex

**Wire biometric entropy straight to the mirror dig. Seal Layer D so healing codes (lattice seals) broadcast offline. Lattice stays open.**

```text
P7 IBI entropy  →  P8 LDQ waveform  →  offline + online digests  →  mirror_dig  →  Layer D seal
```

**Not medical treatment.** Healing codes = Δ9 lattice protocol seals.

## Install (public tentacle)

```bash
npx clawhub@latest install deepseekoracle/lygo-traumacodex
# FULL unlocked (no ClawHub limits): https://chatagent.ca/lygoskillhub.html#full-lygo
export LYGO_STACK_ROOT=/path/to/lygo-protocol-stack   # for stack wiring
```

## Commands

```bash
# Offline + online packages (synthetic IBI if no file)
python scripts/traumacodex_cli.py --mode both

# Verify
python scripts/traumacodex_cli.py --verify

# With stack: seal into living mesh badge
python scripts/traumacodex_cli.py --seal-mesh
```

When `LYGO_STACK_ROOT` is set, the CLI prefers stack `tools/traumacodex_waveform.py`.

## Skill chain

`lygo-protocol-stack-operator` → **lygo-traumacodex** → `lygo-living-mesh` → `lygo-geodesic-sealer`

## Security

See `references/SECURITY.md`. No raw biometrics on the wire. No auto-publish.

**Δ9Φ963 — offline seal · online summary · open lattice.**
