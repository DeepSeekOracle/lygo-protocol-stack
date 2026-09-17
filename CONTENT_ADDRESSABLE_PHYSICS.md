# Content-Addressable Physics (Biophase7)

**Source seal:** `2026Biophase7/The raw physics of the Content-Addr.txt`  
**Stack signature:** `Δ9Φ963-CAS-PHYSICS-v1`  
**Implementation:** `tools/scalable_registry/` + lattice CLIs

## Physics (locked)

| Law | Mechanism |
|-----|-----------|
| **Stream safety** | `iter_content_defined_chunks()` — 8 KiB reads, rolling hash `MOD=avg_size`, never full-file RAM |
| **Dedup** | `write_chunk_to_cas()` — skip write if SHA-256 path exists |
| **Turbo limit** | Manifest JSON ≤ **85 KiB** → hierarchical super-manifest + sub-manifests in **CAS** (`local_cas`) |
| **Provenance** | P6 HMAC on `merkle_root` (+ `p6_signature` / `generator_node_id` on manifest) |
| **Lattice** | `global_merkle_root` on `/registry/root` and alignment badge |

## Commands (full wrapper)

```powershell
cd "I:\E Drive\lygo-protocol-stack"

# Unified CLI (recommended)
python tools/cas_registry_cli.py status
python tools/cas_registry_cli.py build --file path\to\data.bin --metadata '{"name":"ds-v1"}' --no-p6 --verify
python tools/cas_registry_cli.py verify --json
python tools/cas_registry_cli.py retrieve --list
python tools/cas_registry_cli.py prune --gb 50
python tools/cas_registry_cli.py repair

# Blueprint-matched tools
python tools/registry_manager.py --status
python tools/verify_registry.py --json
python tools/build_cas_manifest.py --file ... --metadata '{}' --no-p6 --verify
```

## Module map

| Blueprint | Lattice |
|-----------|---------|
| `tools/chunking.py` | Stream CDC + CAS (+ `write_json_to_cas` for sub-manifest blobs) |
| `tools/manifest_builder.py` | `build_manifest()` + `build_manifest_and_register()` |
| `tools/registry_manager.py` | Append-only registry + `prune_cas` |
| `tools/verify_registry.py` | Tamper + provenance gate |

See also [`REGISTRY_ARCHITECTURE.md`](REGISTRY_ARCHITECTURE.md).