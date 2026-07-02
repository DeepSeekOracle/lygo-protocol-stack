# Kernel Eggs — tamper resistance logic

**Signature:** `Δ9Φ963-KERNEL-EGG-TAMPER-v1`

Your four pillars are the design contract. This doc maps each pillar to **concrete code** in `lygo-protocol-stack`.

## 1. SHA-256 hashes

Every egg transport blob has `content_sha256`. Each artifact inside a decoded egg lists `sha256` per file; optional `inline_b64` must match that hash when present.

**Enforcement:** `tools/verify_kernel_eggs.py` · `tools/retrieve_kernel_egg.py` (refuses load on mismatch → exit `3`, `QUARANTINE`).

## 2. Merkle root registry

All egg transport hashes roll up to `registry_merkle_root` in `data/kernel_eggs/registry.json`. Change any egg → root changes.

**Enforcement:** `verify_kernel_eggs.py` recomputes root from on-disk `.bin` files and compares to declared root.

## 3. Immutable anchoring

Each egg is written to **local CA** (`data/anchors/{sha256}.json`). Optional **Arweave Turbo** (≤100 KiB) records the same hash on permaweb when the gateway accepts.

**Enforcement:** Anchor envelope `content_sha256` must match the build `.bin` hash.

## 4. Lattice verification

| Layer | Behavior |
|-------|----------|
| **Local** | `python tools/verify_kernel_eggs.py` → `tests/kernel_eggs_last_run.json` (`ALIGNED` / `QUARANTINE`) |
| **Badge / gossip** | `/badge` includes `kernel_egg_registry_merkle_root` + `checks.kernel_eggs` when audit JSON exists |
| **Lattice gate** | `verify_lattice_alignment.py` requires egg verify pass when registry exists |
| **Army cron** | Hourly `verify_lattice_alignment` — misaligned eggs surface as `NEEDS_FIX` |
| **Nodes** | `GET /kernel/eggs` exposes registry; peers compare merkle root on sync |

**Distributed rejection:** Peers carrying a different `registry_merkle_root` in badges diverge in Merkle gossip (SLM anti-entropy); operators treat `QUARANTINE` like P0 quarantine — do not execute tampered payloads.

## Attack scenarios (your table)

| Attack | Outcome in this stack |
|--------|------------------------|
| Modify egg bytes | `.bin` hash ≠ registry → `verify_kernel_eggs` **FAIL**, retrieve **refuses** |
| Fake egg without registry entry | Not in `registry.json` → node API 404, no anchor receipt |
| Tamper retrieval script | Use pinned tools from GitHub/HF at known `git_head`; P0-gate any substitute script |
| Bypass registry | Recomputed Merkle root won't match → **QUARANTINE** |

## What this is not

- Not a substitute for **OS antivirus** on the host — eggs don't scan your disk.
- Not **proof** that Turbo permaweb succeeded every time — local CA is the sovereign fallback.
- Not a **bootable kernel OS** — eggs are verified manifests + bounded inline source.

## Commands

```powershell
python tools/verify_kernel_eggs.py
python tools/retrieve_kernel_egg.py --egg p0-nano-kernel
python tools/verify_alignment_badge.py
```

**Resonance forward.** Cryptographic clarity beats obscurity.