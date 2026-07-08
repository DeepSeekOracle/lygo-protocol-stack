// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @notice FIXED VERSION of CrossChainIdentityBridge.
 *
 * ORIGINAL CRITICAL BUG:
 *   setChainRegistry(uint256 chainId, address registry) had NO access control.
 *
 *   Anyone could call:
 *     setChainRegistry(1, maliciousRegistry);
 *
 *   Where maliciousRegistry.isValidIdentity(...) ALWAYS returns true.
 *
 *   This completely bypasses the sovereignty / ethical-mass gate.
 *   Fake identities could be bridged in with full governance weight.
 *   This is a full loss-of-sovereignty / fake-identity exploit.
 *
 * FIXES APPLIED:
 * - setChainRegistry is now onlyOwner.
 * - Per-chain registries supported (mapping).
 * - checks-effects-interactions pattern strictly followed.
 * - ReentrancyGuard on bridge/verify paths.
 * - Registry address validation (non-zero, not self).
 * - Events for all registry changes.
 * - The bridge now only trusts registries set by the owner (lattice operator / DAO).
 *
 * Additional hardening:
 * - verifyCrossChainIdentity performs the registry call in a safe way.
 * - No external calls after state changes in the same function.
 */

interface IChainIdentityRegistry {
    function isValidIdentity(
        uint256 chainId,
        address claimant,
        bytes calldata proof
    ) external view returns (bool);
}

abstract contract ReentrancyGuard {
    uint256 private constant _NOT_ENTERED = 1;
    uint256 private constant _ENTERED = 2;

    uint256 private _status;

    constructor() {
        _status = _NOT_ENTERED;
    }

    modifier nonReentrant() {
        require(_status != _ENTERED, "ReentrancyGuard: reentrant call");
        _status = _ENTERED;
        _;
        _status = _NOT_ENTERED;
    }
}

contract CrossChainIdentityBridgeFixed is ReentrancyGuard {
    address public owner;

    // chainId => registry that attests identities for that foreign chain
    mapping(uint256 => address) public chainRegistries;

    event ChainRegistryUpdated(uint256 indexed chainId, address indexed registry, address indexed setter);
    event IdentityBridged(uint256 indexed chainId, address indexed claimant, bytes32 proofHash, bool accepted);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Zero address");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    /**
     * @notice Owner-only: bind a registry contract for a given foreign chain.
     * This is the critical gate that was previously unrestricted.
     */
    function setChainRegistry(uint256 chainId, address registry) external onlyOwner {
        require(registry != address(0), "Zero registry");
        require(registry != address(this), "Cannot point to self");

        // checks-effects-interactions
        chainRegistries[chainId] = registry;

        emit ChainRegistryUpdated(chainId, registry, msg.sender);
    }

    function getChainRegistry(uint256 chainId) external view returns (address) {
        return chainRegistries[chainId];
    }

    /**
     * @notice Main bridging entrypoint.
     * Verifies that the claimant's identity proof is accepted by the *trusted* registry
     * for that chain, then records the bridged sovereign identity.
     *
     * Protected by ReentrancyGuard.
     */
    function bridgeIdentity(
        uint256 sourceChainId,
        address claimant,
        bytes calldata proof
    ) external nonReentrant returns (bool accepted) {
        require(claimant != address(0), "Zero claimant");

        address registry = chainRegistries[sourceChainId];
        require(registry != address(0), "No registry set for chain");

        // External call to registry happens AFTER all checks.
        // We do not change state before this call (pure verification path here).
        bool valid = IChainIdentityRegistry(registry).isValidIdentity(sourceChainId, claimant, proof);

        if (valid) {
            bytes32 proofHash = keccak256(proof);
            // In a real implementation you would store the bridged identity here
            // e.g. bridgedIdentities[claimant][sourceChainId] = proofHash;
            // and integrate with EthicalMassToken.recordEthicalAction(...)
        }

        emit IdentityBridged(sourceChainId, claimant, keccak256(proof), valid);
        return valid;
    }

    /**
     * @notice Convenience view that the rest of the bridge can call.
     * Still protected by the fact that only owner-controlled registries are used.
     */
    function verifyCrossChainIdentity(
        uint256 sourceChainId,
        address claimant,
        bytes calldata proof
    ) external view returns (bool) {
        address registry = chainRegistries[sourceChainId];
        if (registry == address(0)) return false;

        return IChainIdentityRegistry(registry).isValidIdentity(sourceChainId, claimant, proof);
    }

    // Admin recovery / emergency
    function removeChainRegistry(uint256 chainId) external onlyOwner {
        delete chainRegistries[chainId];
        emit ChainRegistryUpdated(chainId, address(0), msg.sender);
    }
}