# Bridge Security Test Stubs

This directory contains reference implementations and test helpers for the critical access control fixes in the LYGO Blockchain ↔ Lattice bridge.

## Files

- `LatticeAttestor.sol` — Concrete reference implementation of `IIdentityAttestor`.
- `LatticeAttestorTest.sol` — Attack simulation helpers (meant to be ported into Hardhat/Foundry).
- This README.

## The Three Failure Modes These Tests Target

### 1. Unrestricted Mint (EthicalMassToken)

**Before fix:** Anyone could call `mint(anyAddress, hugeAmount, freshHash)`.

**After fix:** No public `mint` or `burn`. Supply only moves through:
- `recordEthicalAction(...)` which **must** pass `attestor.verifyEthicalAction(...)`
- `applyEthicalDecay(...)` (restricted)

**Test expectation:** Any attempt to increase balance without going through a verified `recordEthicalAction` must fail.

### 2. Unrestricted Registry Binding (CrossChainIdentityBridge)

**Before fix:** `setChainRegistry(chainId, evilRegistry)` was callable by anyone. `evilRegistry.isValidIdentity(...)` could always return true.

**After fix:**
- `setChainRegistry` is `onlyOwner`
- Owner is set in constructor to `msg.sender`
- Additional sanity checks (non-zero, not self)

**Test expectation:** Non-owner calls to `setChainRegistry` must revert. Only the bridge owner (the party running the sovereign lattice) can bind registries.

### 3. Stub Attestor / Registry That Always Returns True

Even with `onlyOwner` and internal mint, if the `attestor` contract itself is a stub that ignores the proof and always returns `true`, the system is still broken.

**Reference mitigation:**
- `LatticeAttestor` requires a valid ECDSA signature from a **trusted signer**.
- Trusted signers can only be managed by the attestor owner (which should itself be a high-trust entity: multisig, timelock, or anchored via Vortex consensus).
- In a production system the attestor would also verify Merkle proofs against roots published by the off-chain lattice.

**Test recommendation:**
- Deploy `EthicalMassTokenFixed` with a `MaliciousAlwaysTrueAttestor`.
- Show that if the token owner is compromised, damage is still limited compared to before (no direct mint), but emphasize that the attestor must also be trustworthy.
- Add tests that a signature from a non-trusted key is rejected even if the attestor is "good".

## New Phase 2 Validation Suite (Added)

### Foundry (Solidity) Tests
- `EthicalMassTokenFixed.t.sol` — Tests unauthorized mint attempts, replay, restricted decay, and attestor dependency.
- `CrossChainIdentityBridgeFixed.t.sol` — Tests onlyOwner on `setChainRegistry`, zero/self checks, and prevention of malicious registry binding.

Run:
```bash
forge test --match-contract "EthicalMassTokenFixedTest|CrossChainIdentityBridgeFixedTest" -vv
```

### Hardhat Integration Script
- `bridge-integration.ts` — Full E2E simulation of the **complete basic system**:
  1. Simulate P1 Mycelium shard
  2. Call `bridgeIdentity` (stores identity)
  3. Call `bridgeIdentityAndMint` (cross-chain verify + store + mint via attestor)
  4. Demonstrate attack prevention

The contracts now form a usable basic foundation: others can extend with real registries, full Merkle anchoring, multisig owners, etc.

Run (Hardhat):
```bash
npx hardhat run docs/bridge/test/bridge-integration.ts --network localhost
```

Includes `AlwaysTrueRegistry.sol` mock for attack vector simulation.

## How to Run These

### With Foundry
```bash
forge test --match-contract LatticeAttestorTest -vv
```

### With Hardhat
Copy the contracts into `contracts/`, the test helpers into `test/`, and write JS tests that use `ethers` + `expectRevert`.

Example skeleton (in JS):

```js
it("should block direct mint", async () => {
  // token.mint(...) should not exist or should revert
});

it("only owner can set registry", async () => {
  await expect(bridge.connect(attacker).setChainRegistry(1, evil.address))
    .to.be.revertedWith("Not owner");
});

it("rejects always-true stub when signature check is enforced", async () => {
  // set a malicious attestor and show that unsigned calls still fail
});
```

## Remaining Trust Assumptions

These fixes move us from "anyone can mint or bind anything" to "only the designated owner + a properly implemented attestor can create ethical mass".

The next layer (not implemented here) is:
- Anchoring the trusted signers / attestor address via the on-chain VortexOracle or Merkle roots from the lattice.
- Using threshold signatures or a set of independent oracles instead of a single `owner`.

This reference implementation + the Fixed contracts give you something you can actually compile, deploy in a test environment, and write negative tests against.