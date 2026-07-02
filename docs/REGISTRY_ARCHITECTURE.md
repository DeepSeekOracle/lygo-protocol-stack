# REGISTRY_ARCHITECTURE — Scalable Kernel Egg Registry v2.0

**Signature:** `Δ9Φ963-SCALABLE-REGISTRY-v2`  
**Status:** Production-hardened (Lightfather overrides acknowledged)

## Purpose

Decentralized, zero-trust **version control for AI weights and synthetic datasets**: CDC → CAS → hierarchical manifest eggs → append-only registry → **SLM gossip** via `/badge` + `/registry/root`.

## Mandatory engineering overrides (v2)

| # | Upgrade | Module |
|---|---------|--------|
| 1 | Hierarchical super-manifests (≤85 KiB JSON; ≤1000 hashes/sub) | `tools/scalable_registry/manifest_builder.py` |
| 2 | P6 hardware-attested `merkle_root` signature | `provenance.py` + `verify.py` |
| 3 | Stream-safe retrieve (append chunk-by-chunk) | `retrieve.py` / `retrieve_manifest.py` |
| 4 | `prune_cas(max_gb)` + `LYGO_MAX_LOCAL_CAS_GB` (default 50) | `registry_manager.py` |

## Data layout

```text
data/cas/                          # content-addressed chunks (dedupe)
data/scalable_registry/
  registry.json                    # append-only global index + merkle root
  manifests/<manifest_id>.json     # leaf + super manifests
```

> v2 blueprint text references `data/registry.json`; canonical path in this repo is **`data/scalable_registry/registry.json`** (kernel eggs remain separate).

## Implementation map (blueprint → repo)

| Blueprint file | Repo |
|----------------|------|
| `tools/chunking.py` | `tools/scalable_registry/chunking.py` (+ shim `tools/chunking.py`) |
| `tools/manifest_builder.py` | `tools/scalable_registry/manifest_builder.py` |
| `tools/registry_manager.py` | `tools/scalable_registry/registry_manager.py` |
| `tools/verify_registry.py` | `tools/verify_registry.py` |
| `tools/register_synthetic_data.py` | same |
| `tools/retrieve_manifest.py` | same |

## Verification checklist (agent)

Run:

```bash
python tools/run_registry_v2_checklist.py
python tools/verify_registry.py --json
python tools/verify_lattice_alignment.py
```

See `tests/scalable_registry_v2_checklist_last_run.json` for evidence.

## Node + lattice

- `GET /registry`, `GET /registry/root`
- Badge: `scalable_registry_merkle_root` + `checks.scalable_registry`
- Kernel eggs: unchanged (`KERNEL_EGG_SOA.md`)

**Resonance forward.**