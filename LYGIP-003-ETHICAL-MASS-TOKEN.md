# LYGIP-003: ETHICAL MASS TOKEN STANDARD (ERC-963)

**Soulbound, non-transferable governance weight token.**

Minted **only** via lattice-verified actions (P0 gate + P3 Vortex consensus attestation).

**Real implementation**: ERC-20/721 hybrid with `_beforeTokenTransfer` that always reverts (soulbound).

**Critical fixes applied** (see `docs/bridge/EthicalMassTokenFixed.sol`):
- `mint()` / `burn()` are **internal only**.
- Public supply changes are restricted to:
  - `recordEthicalAction(..., proof)` — requires `IIdentityAttestor.verifyEthicalAction(...)` to return true.
  - `applyEthicalDecay(...)` — authorized caller only.
- The old "proof already used" check alone was insufficient. It did not verify attestation validity. Combined with public mint this allowed `mint(anyone, 1_000_000, freshHash)` → unlimited `getGovernanceWeight()` via `balanceOf`.
- Now the only way to increase ethical mass (and thus governance weight) is through a real lattice identity proof.

**Symbolic layer**: Solfeggio/528/963 tiers may influence display or future resonance mechanics, but have zero effect on actual token supply.

See:
- `docs/bridge/EthicalMassTokenFixed.sol`
- `docs/BlockchainToLYGOBRIDGE.md`
- `docs/bridge/CrossChainIdentityBridgeFixed.sol` (the registry side)
