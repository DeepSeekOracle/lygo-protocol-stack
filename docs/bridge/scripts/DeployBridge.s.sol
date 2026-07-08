// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Script, console2} from "forge-std/Script.sol";
import {LatticeAttestor} from "../LatticeAttestor.sol";
import {EthicalMassTokenFixed} from "../EthicalMassTokenFixed.sol";
import {CrossChainIdentityBridgeFixed} from "../CrossChainIdentityBridgeFixed.sol";
import {VortexOraclePRB} from "../VortexOraclePRB.sol";

/**
 * @title DeployBridge
 * @notice Deterministic deployment and permission-wiring script for the LYGO Sovereign Bridge Suite.
 */
contract DeployBridge is Script {
    // Standard EVM Chain IDs for cross-chain registry mapping
    uint256 public constant ETHEREUM_MAINNET_ID = 1;
    uint256 public constant POLYGON_MAINNET_ID = 137;
    uint256 public constant ARBITRUM_ONE_ID = 42161;

    function run() external {
        // Retrieve deployment private key and admin multisig address from environment
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        address coldStorageAdmin = vm.envOr("ADMIN_MULTISIG", deployer);

        console2.log("==================================================");
        console2.log("Starting LYGO Bridge Suite Deployment");
        console2.log("Deployer Address:", deployer);
        console2.log("Target Admin Vault:", coldStorageAdmin);
        console2.log("==================================================");

        vm.startBroadcast(deployerPrivateKey);

        // Step 1: Deploy LatticeAttestor with initial P0 Nano-Kernel signer authority
        LatticeAttestor attestor = new LatticeAttestor(deployer);
        console2.log("1. LatticeAttestor deployed at:", address(attestor));

        // Step 2: Deploy Soulbound ERC-963 Token, binding the Attestor
        EthicalMassTokenFixed ethicalMassToken = new EthicalMassTokenFixed(
            address(attestor),
            "LYGO Ethical Mass Token",
            "ETHICAL-MASS"
        );
        console2.log("2. EthicalMassTokenFixed deployed at:", address(ethicalMassToken));

        // Step 3: Deploy Cross-Chain Identity Bridge, binding Token and Attestor
        CrossChainIdentityBridgeFixed bridge = new CrossChainIdentityBridgeFixed(
            address(ethicalMassToken),
            address(attestor)
        );
        console2.log("3. CrossChainIdentityBridgeFixed deployed at:", address(bridge));

        // Step 4: Deploy Gas-Optimized PRBMath Vortex Oracle
        VortexOraclePRB oracle = new VortexOraclePRB(address(ethicalMassToken));
        console2.log("4. VortexOraclePRB deployed at:", address(oracle));

        // Step 5: Wire Cross-Chain Registries (Self-referencing for testnet/initial deployment)
        bridge.setChainRegistry(ETHEREUM_MAINNET_ID, address(bridge));
        bridge.setChainRegistry(POLYGON_MAINNET_ID, address(bridge));
        bridge.setChainRegistry(ARBITRUM_ONE_ID, address(bridge));
        console2.log("5. Initial cross-chain registry mappings configured.");

        // Step 6: Initiate 2-Step Ownership Transfer if an external Admin Vault is specified
        if (coldStorageAdmin != deployer) {
            attestor.transferOwnership(coldStorageAdmin);
            ethicalMassToken.transferOwnership(coldStorageAdmin);
            bridge.transferOwnership(coldStorageAdmin);
            oracle.transferOwnership(coldStorageAdmin);
            console2.log("6. Ownership transfer initiated to Admin Vault (Pending Acceptance).");
        } else {
            console2.log("6. Deployer retained as primary Owner.");
        }

        vm.stopBroadcast();
        console2.log("==================================================");
        console2.log("Deployment Complete. All systems wired.");
        console2.log("==================================================");
    }
}