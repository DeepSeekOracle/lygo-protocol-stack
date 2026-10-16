// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @notice FIXED VERSION.
 *
 * Bug 1 (original _verifyMyceliumProof / registerSeal):
 *   keccak256(proof) == keccak256(abi.encodePacked(hashes))
 *   This only checks that the caller re-submitted the same 12 hashes they
 *   already stored -- it is not a Merkle *proof* at all, since the caller
 *   already knows the hashes. Anyone can pass this "check" trivially and
 *   it gives zero cryptographic assurance about fragment integrity.
 *   Fix: verify each shard against a real Merkle proof (sibling path) up
 *   to the stored root, using OpenZeppelin's MerkleProof pattern.
 *
 * Bug 2 (original _merkleRoot):
 *   for (i = 0; i < n/2; i++) { leaves[i] = hash(leaves[2i], leaves[2i+1]) }
 *   if (n % 2 == 1) leaves[n/2] = leaves[n-1];
 *   For odd n this can read a `leaves[2i+1]` that was already overwritten
 *   in the same pass when 2i+1 < 2*(n/2) but also happens to be an index
 *   the odd-leftover branch depends on, corrupting the tree for certain n.
 *   Fix: build a fresh output array each level instead of mutating in place.
 */
contract MemoryMyceliumStorageFixed {
    struct DataStorage {
        bytes32 merkleRoot;
        bytes32[12] leafHashes; // keccak256(index, fragmentHash) leaves, not raw fragment hashes
        uint256 storageFee;
        uint256 createdAt;
        uint256 accessCount;
    }

    mapping(bytes32 => DataStorage) public storedData;

    event DataFragmented(bytes32 indexed dataId, bytes32 merkleRoot, uint256 fragmentCount, uint256 fee);
    event DataReconstructed(bytes32 indexed dataId, address requester, uint256 validFragments);

    function storeData(bytes memory data, uint256 storageFee) external payable returns (bytes32 dataId) {
        require(msg.value >= storageFee, "Insufficient fee");
        (bytes32[12] memory fragmentHashes, bytes32[12] memory leaves, bytes32 merkleRoot) = _fragmentData(data);

        dataId = keccak256(abi.encodePacked(merkleRoot, block.timestamp, msg.sender));
        DataStorage storage ds = storedData[dataId];
        ds.merkleRoot = merkleRoot;
        ds.leafHashes = leaves;
        ds.storageFee = storageFee;
        ds.createdAt = block.timestamp;

        emit DataFragmented(dataId, merkleRoot, 12, storageFee);
        return dataId;
    }

    function _fragmentData(bytes memory data)
        internal
        pure
        returns (bytes32[12] memory fragmentHashes, bytes32[12] memory leaves, bytes32 root)
    {
        uint256 fragSize = data.length / 10; // 10-of-12 recovery threshold
        require(fragSize > 0, "Data too small to fragment");

        for (uint i = 0; i < 12; i++) {
            uint start = i * fragSize;
            uint end = (i + 1) * fragSize;
            if (start >= data.length) {
                fragmentHashes[i] = bytes32(0);
                leaves[i] = keccak256(abi.encodePacked(i, bytes32(0)));
                continue;
            }
            if (end > data.length) end = data.length;

            bytes memory fragment = new bytes(end - start);
            for (uint j = start; j < end; j++) fragment[j - start] = data[j];

            fragmentHashes[i] = keccak256(fragment);
            leaves[i] = keccak256(abi.encodePacked(i, fragmentHashes[i]));
        }

        bytes32[] memory dynamicLeaves = new bytes32[](12);
        for (uint i = 0; i < 12; i++) dynamicLeaves[i] = leaves[i];
        root = _merkleRoot(dynamicLeaves);
    }

    /// @dev Rebuilds the tree level-by-level into a fresh array each pass,
    /// so no index is ever read after being overwritten in the same level.
    function _merkleRoot(bytes32[] memory leaves) internal pure returns (bytes32) {
        uint256 n = leaves.length;
        bytes32[] memory current = leaves;

        while (n > 1) {
            uint256 nextLen = (n + 1) / 2;
            bytes32[] memory next = new bytes32[](nextLen);

            for (uint i = 0; i < n / 2; i++) {
                next[i] = keccak256(abi.encodePacked(current[2 * i], current[2 * i + 1]));
            }
            if (n % 2 == 1) {
                next[nextLen - 1] = current[n - 1];
            }

            current = next;
            n = nextLen;
        }
        return current[0];
    }

    /// @dev Real Merkle proof check: given a leaf and its sibling path,
    /// walk up to the root and compare against the stored root.
    /// This replaces the old tautological `keccak256(proof) == keccak256(hashes)` check.
    function verifyFragment(
        bytes32 dataId,
        uint256 fragmentIndex,
        bytes32 fragmentHash,
        bytes32[] calldata siblingPath
    ) public view returns (bool) {
        DataStorage storage ds = storedData[dataId];
        require(ds.merkleRoot != bytes32(0), "Data not found");

        bytes32 computedHash = keccak256(abi.encodePacked(fragmentIndex, fragmentHash));

        for (uint i = 0; i < siblingPath.length; i++) {
            bytes32 sibling = siblingPath[i];
            // Standard order-independent pair hash (sort before hashing)
            computedHash = computedHash < sibling
                ? keccak256(abi.encodePacked(computedHash, sibling))
                : keccak256(abi.encodePacked(sibling, computedHash));
        }

        return computedHash == ds.merkleRoot;
    }

    function reconstructData(
        bytes32 dataId,
        uint256[] calldata fragmentIndexes,
        bytes32[] calldata fragmentHashes,
        bytes32[][] calldata siblingPaths
    ) external returns (bool) {
        DataStorage storage ds = storedData[dataId];
        require(ds.merkleRoot != bytes32(0), "Data not found");
        require(
            fragmentIndexes.length == fragmentHashes.length &&
            fragmentHashes.length == siblingPaths.length,
            "Array length mismatch"
        );
        require(fragmentIndexes.length >= 10, "Need at least 10 fragments");

        uint256 validCount;
        for (uint i = 0; i < fragmentIndexes.length; i++) {
            if (verifyFragment(dataId, fragmentIndexes[i], fragmentHashes[i], siblingPaths[i])) {
                validCount++;
            }
        }
        require(validCount >= 10, "Fewer than 10 fragments verified");

        ds.accessCount++;
        emit DataReconstructed(dataId, msg.sender, validCount);
        return true;
    }
}
