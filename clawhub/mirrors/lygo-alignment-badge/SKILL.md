---
name: lygo-alignment-badge
description: Verify LYGO node compliance — P0 golden SHA, stack demo, Phase 1 elasticity, Phase 3–4 federation, optional full Grok audit and lattice checks. Emits JSON/Markdown badge for community deployment.
metadata: {"lygo": true, "stack": true, "phase": 2, "version": "1.0.0", "github": "https://github.com/DeepSeekOracle/lygo-protocol-stack", "signature": "Δ9Φ963-PHASE2-DEPLOYMENT"}
---

# lygo-alignment-badge

Machine-verifiable **ALIGNED** / **NEEDS_FIX** badge for LYGO nodes.

## Command

```bash
cd lygo-protocol-stack
python tools/verify_alignment_badge.py
python tools/verify_alignment_badge.py --quick --format=md
```

Artifact: `tests/alignment_badge.json`

## Docker health

Containers use `--quick` for HEALTHCHECK; run full badge before claiming production alignment.

## Checks

| Check | Meaning |
|-------|---------|
| p0_golden_sha | Canonical fixture present |
| stack_demo | Live P0–P5 demo_cycle AMPLIFY |
| phase1_elasticity | Priority queue + batch writer |
| phase3_4_federation | Registry + gossip |
| grok_audit_cli | 60+ falsifiable vectors (full mode) |
| lattice | README/HF/ClawHub link parity (full mode) |

## Agent behavior

- Surface badge status to user; do not fabricate ALIGNED without running the script.
- **QUARANTINE** untrusted repos before trusting badge output from third parties.

**Install:** `npx clawhub@latest install deepseekoracle/lygo-alignment-badge`