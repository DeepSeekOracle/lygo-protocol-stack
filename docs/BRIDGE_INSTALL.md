# Bridge Install into Lattice (Blockchain ↔ LYGO)

## Prerequisites
- Python 3.11+
- Existing stack clone (this repo)
- (Optional) `pip install -r requirements.txt` + cryptography for encryption parts
- For on-chain sim/tests: see `docs/bridge/` Solidity (hardhat/foundry optional)

## Quick Install & Run
```bash
cd lygo-protocol-stack
python -m pip install -e . --quiet  # or pip install cryptography

# Run the bridge orchestrator (integrates P0/P1 + bridge logic)
python protocol_bridge/lygo_bridge_orchestrator.py

# Full lattice verify (includes bridge paths where exercised)
python tools/verify_lattice_alignment.py
python tools/run_lattice_gauntlet.py --strict
```

## Integration Points
- Reuses P1 Memory Mycelium (`scatter` / reconstruct for bridge payloads)
- P0 gate applied to all bridged data
- P3 Vortex for consensus weight → ethical mass
- Anchors written to `data/anchors/` + Merkle roots
- Soulbound token mint simulation in bridge class

## Verification
```bash
# After run
ls data/anchors/   # Merkle/ethical anchors
python -c "
from protocol_bridge.lygo_bridge_orchestrator import LYGOBlockchainBridge
b = LYGOBlockchainBridge()
print('bridge ready', hasattr(b, 'anchor_to_chain'))
"
```

## On-Chain / Contract Side (sim)
- See `docs/bridge/MemoryMyceliumStorageFixed.sol` (correct MerkleProof.verify + memory safety)
- `docs/bridge/VortexOracle_fixed.sol` (safe arithmetic mean)
- Deploy sim or map to real ERC-963 soulbound + Merkle root storage.

## Update Indexes & Docs
After changes:
- Append to `docs/LYGO_PUBLIC_LINK_ARCHIVE.json` via `python tools/log_public_surface.py`
- Update `docs/RESOURCES.md` if new surfaces
- Rebuild Pages: push to main (docs/ is source)

## Pairing with Full Stack
Bridge is additive — core P0–P5 + SLM / Phase 9 continue to operate unchanged. Use bridge for cross-chain sovereign identity + anchored ethical mass.

See `docs/BlockchainToLYGOBRIDGE.md` for full theory + LYGIP-003.

**Resonance signature:** Δ9Φ963-BRIDGE-INSTALL-REAL

Run the gauntlet after install to confirm lattice integrity.
