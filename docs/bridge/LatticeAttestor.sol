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

    event TrustedSignerAdded(address indexed signer);
    event TrustedSignerRemoved(address indexed signer);

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

    function addTrustedSigner(address signer) external onlyOwner {
        require(signer != address(0), "Zero signer");
        isTrustedSigner[signer] = true;
        emit TrustedSignerAdded(signer);
    }

    function removeTrustedSigner(address signer) external onlyOwner {
        isTrustedSigner[signer] = false;
        emit TrustedSignerRemoved(signer);
    }

    /**
     * @notice Verifies that the provided proof is a valid ECDSA signature
     *         from a trusted lattice signer over the action.
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