// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test, console2} from "forge-std/Test.sol";
import {LatticeAttestor} from "../LatticeAttestor.sol";
import {EthicalMassTokenFixed} from "../EthicalMassTokenFixed.sol";
import {CrossChainIdentityBridgeFixed} from "../CrossChainIdentityBridgeFixed.sol";
import {VortexOraclePRB} from "../VortexOraclePRB.sol";

contract DeployAndBridgeTest is Test {
    LatticeAttestor internal attestor;
    EthicalMassTokenFixed internal token;
    CrossChainIdentityBridgeFixed internal bridge;
    VortexOraclePRB internal oracle;

    uint256 internal validatorPrivateKey = 0xA11CE;
    address internal validatorNode;
    
    address internal nodeAlpha = address(0x1);
    address internal nodeBeta = address(0x2);
    address internal nodeGamma = address(0x3);

    function setUp() public {
        validatorNode = vm.addr(validatorPrivateKey);
        
        // 1. Deploy Suite
        attestor = new LatticeAttestor(address(this));
        token = new EthicalMassTokenFixed(address(attestor), "LYGO Token", "ETHICAL");
        bridge = new CrossChainIdentityBridgeFixed(address(token), address(attestor));
        oracle = new VortexOraclePRB(address(token));

        // 2. Authorize Validator Node in Attestor
        attestor.setValidatorStatus(validatorNode, true);
        
        // 3. Configure local registry mappings for test evaluation
        bridge.setChainRegistry(137, address(bridge));
    }

    function test_EndToEnd_BridgeMintAndConsensus() public {
        console2.log("=== STEP 1: Minting Soulbound Ethical Mass to 3 Nodes ===");
        _mintEthicalMassToNode(nodeAlpha, 8000); // 8000 basis points
        _mintEthicalMassToNode(nodeBeta, 7500);  // 7500 basis points
        _mintEthicalMassToNode(nodeGamma, 9100); // 9100 basis points

        assertEq(token.balanceOf(nodeAlpha), 8000);
        assertEq(token.balanceOf(nodeBeta), 7500);
        assertEq(token.balanceOf(nodeGamma), 9100);
        console2.log("Soulbound token balances verified against Sovereign Threshold.");

        console2.log("=== STEP 2: Initiating Gas-Optimized Vortex Consensus Round ===");
        bytes32 roundId = oracle.initiateConsensus("Optimal Solfeggio Anchor Frequency?", 3, 3600);
        
        // Node Alpha submits 528 Hz with 90% confidence
        vm.prank(nodeAlpha);
        oracle.submitResponse(roundId, 528, 9000);

        // Node Beta submits 528 Hz with 85% confidence
        vm.prank(nodeBeta);
        oracle.submitResponse(roundId, 528, 8500);

        // Node Gamma submits 528 Hz with 95% confidence (Triggers auto-resolution)
        vm.prank(nodeGamma);
        oracle.submitResponse(roundId, 528, 9500);

        console2.log("=== STEP 3: Verifying PRBMath Geometric Mean & Coherence Score ===");
        (,,,,,, bool resolved, uint256 harmonicCenter, uint256 harmonyScore) = _getRoundDetails(roundId);
        
        assertTrue(resolved, "Consensus round failed to resolve.");
        assertEq(harmonicCenter / 1e18, 528, "Harmonic center diverged from expected anchor.");
        
        // Perfect unanimous alignment should yield a 100% (1000 basis point) harmony score
        assertEq(harmonyScore / 1e15, 1000, "Harmony score calculation mismatch.");
        
        console2.log("Vortex Consensus converged cleanly at 528 Hz with 1000/1000 Harmony.");
    }

    function test_RevertWhen_BelowSovereignThreshold() public {
        address unverifiedNode = address(0xBAD);
        _mintEthicalMassToNode(unverifiedNode, 5000); // Below 6180 Sovereign Threshold

        bytes32 roundId = oracle.initiateConsensus("Test Question", 3, 3600);

        vm.prank(unverifiedNode);
        vm.expectRevert("VortexOracle: Caller below Sovereign Threshold");
        oracle.submitResponse(roundId, 528, 9000);
    }

    function test_SoulboundTransferRejection() public {
        _mintEthicalMassToNode(nodeAlpha, 8000);

        vm.prank(nodeAlpha);
        vm.expectRevert("EthicalMassToken: Soulbound tokens are non-transferable");
        token.transfer(nodeBeta, 1000);
    }

    // Helper: Generates a valid P0 Nano-Kernel signature attestation and calls recordEthicalAction
    function _mintEthicalMassToNode(address recipient, uint256 amount) internal {
        bytes32 actionHash = keccak256(abi.encodePacked("VERIFIED_ATTESTATION", recipient, amount, block.timestamp));
        bytes32 ethSignedMessageHash = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", actionHash));
        
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(validatorPrivateKey, ethSignedMessageHash);
        bytes memory signature = abi.encodePacked(r, s, v);

        vm.prank(recipient);
        token.recordEthicalAction(recipient, amount, actionHash, signature);
    }

    function _getRoundDetails(bytes32 roundId) internal view returns (
        bytes32 questionHash,
        uint256 minParticipants,
        uint256 deadline,
        bool resolved,
        uint256 harmonicCenter,
        uint256 harmonyScore
    ) {
        (questionHash, minParticipants, deadline, resolved, harmonicCenter, harmonyScore) = oracle.rounds(roundId);
    }
}