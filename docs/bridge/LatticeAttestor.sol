// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @notice REFERENCE IMPLEMENTATION for IIdentityAttestor (used by EthicalMassTokenFixed).
 *
 * This is NOT the final on-chain lattice attestor. It is a concrete, auditable
 * example that demonstrates how verification should work.
 *
 * GOAL: Make the "verifyEthicalAction" call actually do something instead of
 *       being a stub that an attacker can point at a contract that always
 *       returns true.
 *
 * Current reference approach:
 * - The attestor is initialized with one or more trusted "Lattice Signers"
 *   (in a real deployment this would be a multisig, a DAO, or a set of
 *   oracles whose keys are themselves anchored via the Vortex consensus).
 * - To record ethical mass, the caller must present:
 *     1. The action details
 *     2. A valid ECDSA signature over (claimant, ethicalMassDelta, actionHash)
 *        from a currently trusted signer.
 * - Replay is still prevented at the token level (usedProofs).
 *
 * This closes the "just implement a contract that always returns true" vector
 * because the attestor itself now enforces cryptographic proof of origin.
 *
 * In a fuller version you would also:
 * - Verify a Merkle proof against a root published by the off-chain lattice
 *   (anchored via the bridge's Merkle roots).
 * - Check P0 + P3 attestation data.
 * - Use a more sophisticated oracle / threshold signature scheme.
 */

interface IIdentityAttestor {
    function verifyEthicalAction(
        address claimant,
        uint256 ethicalMassDelta,
        bytes32 actionHash,
        bytes calldata proof
    ) external view returns (bool);
}

contract LatticeAttestor is IIdentityAttestor {
    mapping(address => bool) public isTrustedSigner;
    address public owner;
    address public pendingOwner;

    event TrustedSignerAdded(address indexed signer);
    event TrustedSignerRemoved(address indexed signer);
    event OwnershipTransferStarted(address indexed from, address indexed to);
    event OwnershipTransferred(address indexed from, address indexed to);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    constructor(address initialSigner) {
        owner = msg.sender;
        if (initialSigner != address(0)) {
            isTrustedSigner[initialSigner] = true;
            emit TrustedSignerAdded(initialSigner);
        }
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Zero address");
        pendingOwner = newOwner;
        emit OwnershipTransferStarted(owner, newOwner);
    }

    function acceptOwnership() external {
        require(msg.sender == pendingOwner, "Not pending owner");
        address previous = owner;
        owner = pendingOwner;
        pendingOwner = address(0);
        emit OwnershipTransferred(previous, owner);
    }

    function addTrustedSigner(address signer) external onlyOwner {
        require(signer != address(0), "Zero signer");
        isTrustedSigner[signer] = true;
        emit TrustedSignerAdded(signer);
    }

    function removeTrustedSigner(address signer) external onlyOwner {
        isTrustedSigner[signer] = false;
        emit TrustedSignerRemoved(signer);
    }

    // For compatibility with deployment test
    function setValidatorStatus(address validator, bool status) external onlyOwner {
        if (status) {
            isTrustedSigner[validator] = true;
            emit TrustedSignerAdded(validator);
        } else {
            isTrustedSigner[validator] = false;
            emit TrustedSignerRemoved(validator);
        }
    }

    /**
     * @notice Helper for decay attestation (to allow future connection to token decay).
     * Returns true if the signature is valid for a decay action.
     */
    function verifyDecayAttestation(
        address holder,
        uint256 decayAmount,
        bytes32 reasonHash,
        bytes calldata proof
    ) external view returns (bool) {
        return verifyEthicalAction(holder, decayAmount, reasonHash, proof);
    }

    /**
     * @notice Verifies that the provided proof is a valid ECDSA signature
     *         from a trusted lattice signer over the action.
     *
     * This is a trusted-oracle model: it proves a known key signed the tuple.
     * It does NOT yet verify against an on-chain committed Merkle root from the lattice.
     *
     * proof layout (for this reference impl):
     *   abi.encodePacked( v (uint8), r (bytes32), s (bytes32) )
     */
    function verifyEthicalAction(
        address claimant,
        uint256 ethicalMassDelta,
        bytes32 actionHash,
        bytes calldata proof
    ) external view override returns (bool) {
        if (proof.length != 65) return false;

        bytes32 messageHash = keccak256(
            abi.encodePacked(
                "\x19Ethereum Signed Message:\n32",
                keccak256(abi.encode(claimant, ethicalMassDelta, actionHash))
            )
        );

        // Recover signer
        bytes32 r;
        bytes32 s;
        uint8 v;

        assembly {
            r := calldataload(add(proof.offset, 0))
            s := calldataload(add(proof.offset, 32))
            v := byte(0, calldataload(add(proof.offset, 64)))
        }

        address signer = ecrecover(messageHash, v, r, s);
        return isTrustedSigner[signer];
    }

    /**
     * @notice Extended verification that also checks a Merkle proof against a committed root.
     * This moves closer to verifiable computation.
     *
     * @param merkleRoot The on-chain committed root from the lattice (e.g. via bridge anchor).
     * @param leaf The leaf (e.g. keccak of action data).
     * @param proof Merkle sibling path.
     */
    function verifyWithMerkle(
        bytes32 merkleRoot,
        bytes32 leaf,
        bytes32[] calldata proof
    ) public pure returns (bool) {
        bytes32 computed = leaf;
        for (uint i = 0; i < proof.length; i++) {
            bytes32 sibling = proof[i];
            computed = computed < sibling
                ? keccak256(abi.encodePacked(computed, sibling))
                : keccak256(abi.encodePacked(sibling, computed));
        }
        return computed == merkleRoot;
    }

    /**
     * @dev Helper for off-chain code to build the signature payload.
     */
    function getMessageHash(
        address claimant,
        uint256 ethicalMassDelta,
        bytes32 actionHash
    ) external pure returns (bytes32) {
        return keccak256(abi.encode(claimant, ethicalMassDelta, actionHash));
    }
}