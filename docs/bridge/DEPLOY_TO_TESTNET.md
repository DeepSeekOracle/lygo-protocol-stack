# Deploy LYGO Bridge to Testnet (Amoy / Sepolia)

**Goal**: Deploy the fixed bridge contracts (post-audit) to Polygon Amoy or Ethereum Sepolia using the Foundry script.

## Prerequisites

- [Foundry](https://book.getfoundry.sh/getting-started/installation) installed (`forge`, `cast`, `anvil`)
- Wallet with test ETH / MATIC (see faucets below)
- Private key (never commit real keys)

```bash
# Install Foundry (if not present)
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

## 1. Get Testnet Funds

### Polygon Amoy (recommended for speed & low cost)
- Chain ID: `80002`
- RPC: `https://rpc-amoy.polygon.technology`
- Faucets:
  - https://faucet.polygon.technology/ (select Amoy)
  - https://www.alchemy.com/faucets/polygon-amoy
  - https://faucet.quicknode.com/polygon/amoy

### Ethereum Sepolia
- Chain ID: `11155111`
- RPC: `https://rpc.sepolia.org` or Alchemy/Infura
- Faucets:
  - https://sepoliafaucet.com/
  - https://www.alchemy.com/faucets/ethereum-sepolia

## 2. Prepare Environment

```bash
cd lygo-protocol-stack/docs/bridge

# Export your deployer key (use a fresh testnet-only key)
export PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE

# Optional: Use a cold multisig/admin address for ownership transfer
export ADMIN_MULTISIG=0xYourAdminAddress
```

**Never use a mainnet private key.**

## 3. Deploy with the Script

The script (`scripts/DeployBridge.s.sol`) deploys in order:

1. `LatticeAttestor`
2. `EthicalMassTokenFixed` (bound to attestor)
3. `CrossChainIdentityBridgeFixed` (bound to token + attestor)
4. `VortexOraclePRB`
5. Wires initial registries (self for testnet)
6. (Optional) Initiates 2-step ownership transfer to `ADMIN_MULTISIG`

### For Polygon Amoy

```bash
forge script scripts/DeployBridge.s.sol \
  --rpc-url https://rpc-amoy.polygon.technology \
  --broadcast \
  --verify \
  -vvvv
```

### For Ethereum Sepolia

```bash
forge script scripts/DeployBridge.s.sol \
  --rpc-url https://rpc.sepolia.org \
  --broadcast \
  --verify \
  -vvvv
```

Add `--legacy` if you run into EIP-1559 issues on some networks.

## 4. After Deployment

The script will print addresses. Copy them.

Example output (truncated):

```
1. LatticeAttestor deployed at: 0x...
2. EthicalMassTokenFixed deployed at: 0x...
3. CrossChainIdentityBridgeFixed deployed at: 0x...
...
```

### Verify on Explorer (if --verify didn't work)

```bash
# Amoy
forge verify-contract <ATTESTOR_ADDRESS> LatticeAttestor --chain-id 80002 --verifier-url https://api-amoy.polygonscan.com/api

# Similar for others
```

## 5. Post-Deployment Steps

1. **Accept ownership** (if you used ADMIN_MULTISIG):
   ```bash
   cast send <CONTRACT> "acceptOwnership()" --private-key $PRIVATE_KEY --rpc-url ...
   ```

2. **Add trusted signers** to the Attestor (use the deployer or your Lattice signer keys):
   ```bash
   cast send <ATTESTOR> "addTrustedSigner(address)" <SIGNER_ADDRESS> --private-key $PRIVATE_KEY ...
   ```

3. **Test the Python bridge orchestrator** (sends 9-Node attestation data):
   ```bash
   cd ../../..
   python protocol_bridge/lygo_bridge_orchestrator.py
   ```

4. **Wire real registries** later (replace the self-references with actual on-chain identity registries).

## 6. Common Flags & Tips

- `--broadcast` actually sends txs
- `-vvvv` for maximum verbosity
- Use `cast` to interact after deploy:
  ```bash
  cast call <TOKEN> "balanceOf(address)" <ADDRESS> --rpc-url ...
  ```
- For production, use a hardware wallet or multisig as owner.

## Faucet Links (Quick)

- **Amoy**: https://faucet.polygon.technology/
- **Sepolia**: https://sepoliafaucet.com/
- **General testnet faucets**: https://chainlist.org/ (filter testnets)

## Next After Deploy

- Update your Python orchestrator with the deployed addresses.
- Run the 9-Node cascade pilot and push the attestation on-chain via `recordEthicalAction`.
- Monitor events for `EthicalMassMinted`, `SealRegistered`, etc.

See also:
- `docs/bridge/AUDIT_FINDINGS.md`
- `docs/BlockchainToLYGOBRIDGE.md`
- `protocol_bridge/lygo_bridge_orchestrator.py` (the `synchronize_9node_enneagram_to_evm` method)

**Status**: This is the current "basic foundation" deployment path. Real cross-chain relayers (CCIP, LayerZero, etc.) can be added later.
