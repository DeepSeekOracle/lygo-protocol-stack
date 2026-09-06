// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @notice FIXED VERSION of EthicalMassToken (LYGIP-003 soulbound governance token).
 *
 * ORIGINAL BUGS (critical access-control / sovereignty bypass):
 *
 * 1. mint() and burn() were external with ZERO access control.
 *    - Anyone could call: mint(victim, 1_000_000, freshHash)
 *    - The only "protection" was a replay check on `usedProofs[proofHash]`.
 *    - It never verified that the proof actually came from a real lattice P0+P3 attestation.
 *    - Since getGovernanceWeight() simply returned balanceOf(), this let attackers
 *      print unlimited voting/governance weight.
 *
 * 2. Direct mint/burn defeated the entire "ethical mass must be earned via verified actions" model.
 *
 * FIXES:
 * - mint() and burn() are now internal only.
 * - The ONLY public paths that can change supply are:
 *     recordEthicalAction(...)  -- gated by a real identity/attestation check
 *     applyEthicalDecay(...)    -- controlled decay (e.g. time or council)
 * - Added proper proof verification hook (IIdentityAttestor).
 * - UsedProofs now part of a verified flow, not the only guard.
 * - Soulbound: transfers always revert.
 * - Emits events for auditability.
 *
 * This is the single most dangerous class of bug in a sovereignty/governance token:
 * unrestricted mint == complete loss of meaning for "ethical mass".
 */

interface IIdentityAttestor {
    /// @notice Returns true only if the proof is a valid lattice-attested action for the claimant.
    function verifyEthicalAction(
        address claimant,
        uint256 ethicalMassDelta,
        bytes32 actionHash,
        bytes calldata proof
    ) external view returns (bool);
}

contract EthicalMassTokenFixed {
    string public name = "LYGO Ethical Mass";
    string public symbol = "LYGO-ETHM";

    mapping(address => uint256) private _balances;
    mapping(bytes32 => bool) public usedProofs;           // replay protection (now inside verified path)

    address public owner;
    address public pendingOwner;
    IIdentityAttestor public attestor;

    uint256 public totalSupply;

    event Transfer(address indexed from, address indexed to, uint256 value); // for ERC20-like compatibility
    event EthicalMassMinted(address indexed to, uint256 amount, bytes32 actionHash);
    event EthicalMassBurned(address indexed from, uint256 amount, bytes32 reasonHash);
    event AttestorUpdated(address indexed newAttestor);
    event OwnershipTransferStarted(address indexed from, address indexed to);
    event OwnershipTransferred(address indexed from, address indexed to);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    constructor(address initialAttestor) {
        owner = msg.sender;
        if (initialAttestor != address(0)) {
            attestor = IIdentityAttestor(initialAttestor);
        }
    }

    // Overload for full compatibility with deployment scripts
    constructor(address initialAttestor, string memory _name, string memory _symbol) {
        owner = msg.sender;
        name = _name;
        symbol = _symbol;
        if (initialAttestor != address(0)) {
            attestor = IIdentityAttestor(initialAttestor);
        }
    }

    function setAttestor(address newAttestor) external onlyOwner {
        attestor = IIdentityAttestor(newAttestor);
        emit AttestorUpdated(newAttestor);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Zero owner");
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

    // ====================== SOULBOUND ======================
    // Transfers are forbidden. This is the core of "soulbound ethical mass".
    function transfer(address /*to*/, uint256 /*amount*/) external pure returns (bool) {
        revert("EthicalMassToken: Soulbound tokens are non-transferable");
    }

    function approve(address /*spender*/, uint256 /*amount*/) external pure returns (bool) {
        revert("Soulbound: approvals disabled");
    }

    function transferFrom(address /*from*/, address /*to*/, uint256 /*amount*/) external pure returns (bool) {
        revert("EthicalMassToken: Soulbound tokens are non-transferable");
    }

    // ====================== PUBLIC SUPPLY MOVEMENT (GATED) ======================

    /**
     * @notice Records a verified ethical action from the lattice.
     * Only this (and decay) can increase supply.
     * The attestor must cryptographically confirm the action came from the sovereign lattice.
     */
    function recordEthicalAction(
        address recipient,
        uint256 ethicalMassDelta,
        bytes32 actionHash,
        bytes calldata proof
    ) external returns (uint256 newBalance) {
        require(recipient != address(0), "Zero recipient");
        require(ethicalMassDelta > 0, "Delta must be > 0");
        require(!usedProofs[actionHash], "Proof already used");

        // Critical: real verification, not just replay check
        require(address(attestor) != address(0), "No attestor set");
        require(
            attestor.verifyEthicalAction(recipient, ethicalMassDelta, actionHash, proof),
            "Invalid lattice attestation"
        );

        usedProofs[actionHash] = true;

        _mint(recipient, ethicalMassDelta);

        emit EthicalMassMinted(recipient, ethicalMassDelta, actionHash);
        return _balances[recipient];
    }

    /**
     * @notice Applies ethical decay (time-based, council-enforced, or penalty).
     *
     * IMPORTANT: Currently only callable by owner.
     * The attestor path was removed because LatticeAttestor has no mechanism
     * to trigger decay (it is a pure view verifier today).
     *
     * Future: Add attestation-gated decay (e.g. via a separate decayProof).
     * For now, decay is a privileged administrative action.
     */
    function applyEthicalDecay(
        address holder,
        uint256 decayAmount,
        bytes32 reasonHash
    ) external returns (uint256 newBalance) {
        require(msg.sender == owner, "Not authorized for decay");
        require(holder != address(0), "Zero holder");
        require(decayAmount > 0, "Decay must be > 0");
        require(_balances[holder] >= decayAmount, "Insufficient balance");

        _burn(holder, decayAmount);

        emit EthicalMassBurned(holder, decayAmount, reasonHash);
        return _balances[holder];
    }

    // ====================== INTERNAL SUPPLY LOGIC ======================

    function _mint(address to, uint256 amount) internal {
        totalSupply += amount;
        _balances[to] += amount;
        emit Transfer(address(0), to, amount);
    }

    function _burn(address from, uint256 amount) internal {
        totalSupply -= amount;
        _balances[from] -= amount;
        emit Transfer(from, address(0), amount);
    }

    // ====================== VIEW FUNCTIONS ======================

    function balanceOf(address account) public view returns (uint256) {
        return _balances[account];
    }

    /**
     * @notice Governance weight is derived strictly from verified ethical mass balance.
     * No direct mint path exists to inflate this.
     */
    function getGovernanceWeight(address account) external view returns (uint256) {
        return _balances[account];
    }

    function isProofUsed(bytes32 actionHash) external view returns (bool) {
        return usedProofs[actionHash];
    }
}