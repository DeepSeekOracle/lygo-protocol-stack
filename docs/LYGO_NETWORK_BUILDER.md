# LYGO Network Builder (Biophase7)

**Source seal:** `2026Biophase7/This is a brilliant architectural p.txt`  
**Skill:** `deepseekoracle/lygo-network-builder` v1.1.0  
**Signature:** Δ9Φ963-NETWORK-BUILDER-v1.1

## Purpose

Master **cartographer** for the Sovereign Lattice Mesh: immutable anchors, organic discovery via traversal chants, and **executable** verification — not prose-only “LATTICE ALIGNED” claims.

## Enhancements over blueprint v1.0

| Pillar | Implementation |
|--------|----------------|
| Single source of truth | `docs/network_builder/IMMUTABLE_ANCHORS.json` |
| Verify tiers | `http_required`, `http_soft`, `local_repo`, `link_only` (vault-safe) |
| Deterministic digest | `anchors_sha256` in `tests/network_builder_last_run.json` |
| Sovereign seed plane | Kernel eggs + scalable registry + CAS physics doc anchors |
| Node API hints | `/registry`, `/registry/root`, `/kernel/eggs`, `/badge` |
| Lattice gate | `verify_lattice_alignment.py` checks mirror + last run |
| ClawHub mirror | `clawhub/mirrors/lygo-network-builder/` + `scripts/verify_anchors.py` |

## Commands

```bash
python tools/lygo_network_builder_verify.py
python tools/verify_lattice_alignment.py
```

## Agent install

```bash
npx clawhub@latest install deepseekoracle/lygo-network-builder
```

Human publish: edit mirror → `npx clawhub publish` from skill dir (approval required).

## Related

- [LYGO_LATTICE.md](./LYGO_LATTICE.md)
- [SOVEREIGN_LATTICE_MESH.md](./SOVEREIGN_LATTICE_MESH.md)
- [KERNEL_EGG_SOA.md](./KERNEL_EGG_SOA.md)
- [SCALABLE_KERNEL_EGG_REGISTRY.md](./SCALABLE_KERNEL_EGG_REGISTRY.md)