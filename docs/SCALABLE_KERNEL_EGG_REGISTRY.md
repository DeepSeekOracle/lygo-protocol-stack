# Scalable Kernel Egg Registry (Synthetic Data & AI Weights)

**Signature:** `Δ9Φ963-SCALABLE-REGISTRY-v1`  
**Blueprint source:** Lightfather's Voice — Complete Blueprint (Biophase7)  
**Engineering overrides:** hierarchical manifests ≤90 KiB, P6 provenance, stream retrieve, `prune_cas`

## v1 priority (shipped)

1. **Manifest generator + CAS layer** — `tools/scalable_registry/chunking.py`, `manifest_builder.py`
2. **Append-only registry CLI** — `register_synthetic_data.py`, `verify_registry.py`, `registry_manager_cli.py`

## Architecture

```text
Application (P1/P3/P5/P7, trainers)
    → CDC chunking → data/cas/ (dedupe)
    → Manifest egg (≤90 KiB JSON) [+ Super-Manifest if huge hash lists]
    → P6 sign merkle_root → append data/scalable_registry/registry.json
    → global_merkle_root on GET /badge (via verify_alignment_badge) + GET /registry/root
    → SLM gossip compares roots (same pattern as kernel eggs)
```

## Four mandatory upgrades

| # | Upgrade | Implementation |
|---|---------|----------------|
| 1 | Hierarchical super-manifests | `_fit_chunk_batches()` + on-disk sub-manifests; super-manifest holds refs only |
| 2 | P6 provenance | `provenance.sign_merkle_root()` — HMAC over `merkle_root` with TPM/PUF-derived key |
| 3 | Stream-safe retrieve | `retrieve.py` — 1 MiB read/write loop + per-chunk SHA-256 |
| 4 | CAS GC | `registry_manager.prune_cas(max_gb)` — LRU by atime; protects manifest-referenced chunks |

## Commands

```powershell
cd "I:\E Drive\lygo-protocol-stack"

# Register (streams large files; safe for multi-GB)
python tools/register_synthetic_data.py --file path\to\weights.safetensors --metadata "{\"name\":\"checkpoint-v1\"}" --anchor

# Verify registry + write tests/scalable_registry_last_run.json
python tools/verify_registry.py --json

# Retrieve (exit 3 on tamper)
python tools/retrieve_manifest.py --id <manifest_id> --out restored.bin

# CAS status / prune (community nodes)
python tools/registry_manager_cli.py --status
python tools/registry_manager_cli.py --prune-cas-gb 50
```

## Node API

- `GET /registry` — entry index + `global_merkle_root`
- `GET /registry/root` — root only (for SLM badge gossip)

## Limits (honest)

| Item | Limit |
|------|--------|
| Single manifest JSON | **≤ 90 KiB** (Turbo free tier headroom) |
| Dataset size | **Unbounded** via CDC + hierarchical manifests |
| Peer provenance | Generator must pass **P0 golden** + P6 signature |
| CAS on node | **Bounded** via `prune_cas`; chunks re-fetchable from network |

## Lattice

`verify_lattice_alignment.py` runs `verify_registry.py` when tools are present.

## Related

- Core kernel eggs (protocol manifests): [`KERNEL_EGG_SOA.md`](KERNEL_EGG_SOA.md)
- SLM gossip: [`SOVEREIGN_LATTICE_MESH.md`](SOVEREIGN_LATTICE_MESH.md)
- Phase 6 attestation: `protocol6_quantum_attest/`