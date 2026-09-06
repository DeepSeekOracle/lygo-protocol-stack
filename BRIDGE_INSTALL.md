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

## On-Chain / Contract Side (sim + hardened)
- `docs/bridge/MemoryMyceliumStorageFixed.sol` — real MerkleProof + safe tree construction
- `docs/bridge/VortexOracle_fixed.sol` — overflow-safe weighted arithmetic mean
- `docs/bridge/EthicalMassTokenFixed.sol` — soulbound, mint **only** via `recordEthicalAction` gated by identity attestor
- `docs/bridge/CrossChainIdentityBridgeFixed.sol` — `setChainRegistry` is `onlyOwner`, ReentrancyGuard, checks-effects-interactions
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

## Testnet Deployment (Polygon Amoy / Ethereum Sepolia) - Roadmap
1. Use Hardhat or Foundry:
   ```bash
   npx hardhat deploy --network amoy   # or sepolia
   ```
2. Deploy:
   - ERC963Implementation.sol (soulbound base)
   - MemoryMyceliumStorageFixed.sol
   - VortexOracleFixed.sol (with PRBMath once integrated)
   - CrossChainIdentityBridgeFixed.sol
   - EthicalMassTokenFixed.sol
3. Verify source on Polygonscan / Etherscan for transparency.
4. Update `protocol_bridge/lygo_bridge_orchestrator.py` with deployed addresses.
5. Wire events as described above.
6. Anchor first seals using the LYGO-SEAL-004-BRIDGE payload format.

Recommended networks:
- Polygon Amoy (chainId 80002) for low-cost testing
- Ethereum Sepolia for broader EVM compatibility testing

See `docs/BlockchainToLYGOBRIDGE.md` and `tests/test_bridge_lattice.py` for validation.
