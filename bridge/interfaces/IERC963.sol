// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC963 {
    function balanceOf(address account) external view returns (uint256);
    // Add other methods as needed for the token
}