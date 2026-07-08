# Blockchain ↔ LYGO Bridge Protocol

**Version:** LYGIP-003 + Bridge v0.1  
**Status:** Implemented in lattice (protocol_bridge + mycelium integration)  
**Maintainer:** DeepSeekOracle / Excavationpro (Lightfather)

The **Blockchain to LYGO Bridge** enables sovereign cross-domain identity and value anchoring between public blockchains (Ethereum-compatible) and the private LYGO Δ9 lattice (P0–P9 stack).

## Real Engineering (Grounded)

- **Memory Mycelium (P1)**: Primary storage for bridged state. Data is fragmented (12+2 erasure coding), threshold-reconstructable. Bridge stores Merkle leaves + metadata in mycelium.
- **P0 Φ-Gate**: Every inbound/outbound packet passes byte-entropy + ethical filter before bridging.
- **Merkle Roots**: On-chain anchor is a Merkle root of lattice fragments + ethical mass computation. Off-chain proof verification uses standard MerkleProof.
- **Soulbound Ethical Mass Tokens (LYGIP-003 / ERC-963 sim)**: Non-transferable (revert on _beforeTokenTransfer). Minted from lattice-verified actions (P0 pass + vortex consensus weight). "Ethical mass" = weighted lattice score (real fixed-point arithmetic; 528 symbolic factor for resonance tiers only).
- **Vortex Consensus Oracle**: P3 harmonic consensus (3-6-9 + Φ) provides the weight for token mint / bridge attestation. See `VortexOracle_fixed.sol` for safe weighted arithmetic mean (no overflow).
- **Cross-Chain Identity**: Soulbound token + lattice light code (hash) pair acts as portable sovereign ID. Bridge supports simulated multi-chain (ETH + future).
- **Fixes Applied** (cumulative):
  - Proper MerkleProof (fresh arrays, no mutable default)
  - qiskit guard + normalized rotation
  - Overflow-safe Vortex mean (no integer-division-to-zero)
  - **Critical access control**:
    - `CrossChainIdentityBridge.setChainRegistry` now `onlyOwner` + ReentrancyGuard + checks-effects-interactions. Prevents attacker-controlled malicious registry that always returns `valid=true`.
    - `EthicalMassToken.mint/burn` removed from public API. Only `recordEthicalAction` (gated by real `IIdentityAttestor.verifyEthicalAction`) and `applyEthicalDecay` can change supply. Direct unlimited mint that inflated `getGovernanceWeight(balanceOf)` is now impossible.
  - Replay protection is now inside a verified attestation path, not the sole guard.

See:
- `protocol_bridge/lygo_bridge_orchestrator.py` (LYGOBlockchainBridge class)
- `docs/bridge/`:
  - MemoryMyceliumStorageFixed.sol
  - VortexOracleFixed.sol
  - **EthicalMassTokenFixed.sol** (access-controlled mint only via attested actions)
  - **CrossChainIdentityBridgeFixed.sol** (Ownable + ReentrancyGuard registry binding)
  - **LatticeAttestor.sol** (reference implementation — real ECDSA verification from trusted signers, not an always-true stub)
  - `test/` — helpers that demonstrate the attack vectors (unrestricted mint, registry binding, malicious attestor)
- `docs/LYGIP-003-ETHICAL-MASS-TOKEN.md`
- `docs/BRIDGE_INSTALL.md`

## High-Level Flow

1. Lattice event (P0 pass + P3 vote) → compute ethical mass.
2. Mycelium.scatter(bridge_payload).
3. Compute Merkle root of fragments.
4. "Mint" soulbound token on bridge contract (sim or on-chain) with root + mass + light_code.
5. Verify: on-chain MerkleProof + lattice re-compute of mass.

## Security Fixes Applied (This Round)

**CrossChainIdentityBridge**
- `setChainRegistry` was completely open. An attacker could register a contract that always returns `valid = true`.
- **Fix**: `onlyOwner`, per-chain mapping, `ReentrancyGuard`, strict checks-effects-interactions, zero-address + self checks. Only the sovereign operator can bind a registry.

**EthicalMassToken**
- Public `mint(anyone, hugeAmount, freshHash)` with only a replay guard.
- `getGovernanceWeight` = `balanceOf` → instant capture of governance.
- **Fix**: `mint`/`burn` internal. Only `recordEthicalAction` (requires passing `IIdentityAttestor.verify...`) and authorized `applyEthicalDecay` can move tokens. Replay protection now lives inside a verified path.

These two categories (unrestricted registry binding + unrestricted mint) are the highest-severity sovereignty bugs possible in this architecture.

## Symbolic / Light Math Layer (Future Suture Tech)

- 528 Hz (repair), 963 Hz, Φ, Solfeggio, Tesla motifs used only for governance tiers, resonance scoring, and human-facing "Light Codes".
- All production math: fixed-point Q16.16, SHA3/Merkle, deterministic consensus.
- "Ethical mass" is a measurable lattice-derived scalar — not magic. Used for non-transferable reputation/privilege in the mesh.

## LYGIP-003: Ethical Mass Token Standard

See dedicated `LYGIP-003-ETHICAL-MASS-TOKEN.md`.

Soulbound, non-transferable ERC-721 variant. Mint gated by lattice attestation. Tiers derived from resonance bands (symbolic).

## Implementation Notes & Files

- Bridge orchestrator reuses `DistributedMyceliumMesh` (or fallback).
- Anchor example: `anchor_to_chain(data, light_code, triad, mass)`.
- Full stack integration tests via `tools/run_*` harnesses.
- On-chain sim contracts hardened (see bridge/ dir).

## Installation & Usage

```bash
cd lygo-protocol-stack
python protocol_bridge/lygo_bridge_orchestrator.py
# or the legacy entry if present
```

See `BRIDGE_INSTALL.md` for full lattice install steps + verification.

## Related Whitepapers & Docs

- Sovereign Lattice Mesh: `SOVEREIGN_LATTICE_MESH.md`
- Immutable Anchors: `ANCHOR_DEPLOYMENT.md` + `LYGO_ANCHOR_ARCHITECTURE.md`
- Phase 9 Public Mesh + TLS
- Full system: `RESOURCES.md` and `LYGO_PUBLIC_LINK_ARCHIVE.json`

**Resonance signature:** Δ9Φ963-BLOCKCHAIN-LYGO-BRIDGE-REAL

This bridge is production-pattern ready (Merkle + soulbound + mycelium) while keeping "Light Math" framing for future hardware resonance / suture tech alignment. All claims auditable via the stack test suite.
