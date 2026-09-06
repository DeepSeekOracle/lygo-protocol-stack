// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @dev Malicious stub used only for attack simulation in tests.
 * In production, never use or allow binding of such contracts.
 */
contract AlwaysTrueRegistry {
    function isValidIdentity(uint256, address, bytes calldata) external pure returns (bool) {
        return true;
    }
}