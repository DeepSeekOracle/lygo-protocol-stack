# Kernel Egg SOA — what we can and cannot store

**Signature:** `Δ9Φ963-KERNEL-EGG-SOA-v1`  
**Tamper logic:** [`KERNEL_EGG_TAMPER_LOGIC.md`](KERNEL_EGG_TAMPER_LOGIC.md)

## Honest answer

| Goal | Feasible? |
|------|-----------|
| Long-term **manifest** of kernel/protocol/driver **hashes** + retrieval URLs on free Turbo (&lt;100 KiB/tx) | **Yes** — done |
| **Local sovereign copy** of egg bytes in `data/anchors/` (content-addressed) | **Yes** — always |
| **Inline** small P0/firmware sources inside one egg (&lt;100 KiB compressed) | **Yes** — `p0-nano-kernel`, `firmware-p04-drivers`, etc. |
| Full **1.4 MB LDQ vault**, entire repo, or videos on free Turbo only | **No** — use GitHub/HF + hash pins; optional web3.storage |
| A **bootable lattice kernel OS** retrieved only from permaweb | **No** — not this architecture |
| **SOA retrieval** via node API + Pages + permaweb registry | **Yes** |

## Eggs (catalog)

| `egg_id` | Contents |
|----------|----------|
| `p0-nano-kernel` | P0 core, LYRA kernel, golden SHA |
| `stack-anchor-hook` | Stack anchor orchestrator + STACK_STATUS |
| `stack-orchestrator-slim` | `lygo_stack.py` hash (+ inline when fits) |
| `lattice-soa-index` | Intel index + lattice map + link archive |
| `firmware-p04-drivers` | P0.4 gate, updatefeed, firmware kernel (E:\\2026) |
| `protocol-drivers-p2-p5` | P2–P5 Python drivers |

## ClawHub skill (voluntary planters)

```bash
npx clawhub@latest install deepseekoracle/lygo-kernel-egg-planter
export LYGO_STACK_ROOT=/path/to/lygo-protocol-stack
python scripts/plant_with_consent.py --i-consent --surfaces local,turbo,registry,clawhub,pages
```

## Commands

```powershell
cd "I:\E Drive\lygo-protocol-stack"
python tools/build_kernel_eggs.py
python tools/anchor_kernel_eggs.py
python tools/retrieve_kernel_egg.py --list
```

## Lattice / nodes

- **Nodes** expose `GET /kernel/eggs` and `GET /kernel/egg/{id}` (port 8787).
- **Gossip pin** can carry `registry_merkle_root` for peers to compare (same pattern as TLS pins).
- **Others** verify eggs via public `docs/KernelEggRegistry.json` on GitHub Pages, then clone repo at `git_head` and check `sha256` lists.

## Web

- [KernelEggRetrieval.html](KernelEggRetrieval.html) — browser view of registry
- Rebuild refreshes `docs/KernelEggRegistry.json`

## Free anchoring

`AnchorProfile.free_max_bytes` = **102400**. Eggs are sharded to stay under limit. Turbo upload is best-effort; **Local CA never fails offline**.