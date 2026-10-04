// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {UD60x18, ud, wrap} from "prb-math/UD60x18.sol";
import {IERC963} from "./interfaces/IERC963.sol";

/**
 * @title VortexOraclePRB
 * @notice Gas-optimized 3-6-9 Vortex Consensus Engine utilizing PRBMathUD60x18 for precision fixed-point arithmetic.
 */
contract VortexOraclePRB {
    struct Response {
        address participant;
        UD60x18 proposal;       // Proposed numerical value (e.g., 528.000000000000000000 Hz)
        UD60x18 confidence;     // Confidence percentage scaled 0 to 1 (e.g., 0.95 = 95%)
        UD60x18 ethicalMass;    // Snapshot of user's Soulbound Ethical Mass at submission time
    }

    struct ConsensusRound {
        bytes32 questionHash;
        uint256 minParticipants;
        uint256 deadline;
        bool resolved;
        UD60x18 harmonicCenter; // Calculated weighted geometric mean
        UD60x18 harmonyScore;   // System coherence score (0.00 to 1.000)
        Response[] responses;
    }

    IERC963 public immutable ethicalMassToken;
    address public owner;
    address public pendingOwner;

    // Minimum Sovereign Threshold in fixed-point (6180 basis points = 618.0)
    UD60x18 public constant SOVEREIGN_THRESHOLD = UD60x18.wrap(618_000_000_000_000_000_000);
    
    // Minimum Harmony Coherence Threshold (0.700 = 70.0%)
    UD60x18 public constant MIN_HARMONY_THRESHOLD = UD60x18.wrap(700_000_000_000_000_000);

    mapping(bytes32 => ConsensusRound) public rounds;
    mapping(bytes32 => mapping(address => bool)) public hasParticipated;

    event ConsensusInitiated(bytes32 indexed roundId, string question, uint256 minParticipants, uint256 deadline);
    event ResponseSubmitted(bytes32 indexed roundId, address indexed participant, uint256 proposal);
    event ConsensusResolved(bytes32 indexed roundId, uint256 harmonicCenter, uint256 harmonyScore, uint256 participants);
    event OwnershipTransferStarted(address indexed previousOwner, address indexed newOwner);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    modifier onlyOwner() {
        require(msg.sender == owner, "VortexOracle: Caller not owner");
        _;
    }

    constructor(address _tokenAddress) {
        require(_tokenAddress != address(0), "VortexOracle: Zero token address");
        ethicalMassToken = IERC963(_tokenAddress);
        owner = msg.sender;
    }

    function initiateConsensus(
        string calldata question,
        uint256 minParticipants,
        uint256 durationSecs
    ) external returns (bytes32 roundId) {
        require(minParticipants >= 3, "VortexOracle: Minimum 3 participants required (3-6-9 rule)");

        roundId = keccak256(abi.encodePacked(question, block.timestamp, msg.sender));
        require(rounds[roundId].deadline == 0, "VortexOracle: Round already exists");

        ConsensusRound storage round = rounds[roundId];
        round.questionHash = keccak256(bytes(question));
        round.minParticipants = minParticipants;
        round.deadline = block.timestamp + durationSecs;

        emit ConsensusInitiated(roundId, question, minParticipants, round.deadline);
    }

    function submitResponse(
        bytes32 roundId,
        uint256 rawProposal,
        uint256 rawConfidenceBasisPoints
    ) external {
        ConsensusRound storage round = rounds[roundId];
        require(block.timestamp <= round.deadline, "VortexOracle: Round deadline passed");
        require(!round.resolved, "VortexOracle: Round already resolved");
        require(!hasParticipated[roundId][msg.sender], "VortexOracle: Already participated");
        require(rawConfidenceBasisPoints <= 10000, "VortexOracle: Confidence exceeds 100%");

        // Validate caller's Soulbound Ethical Mass
        uint256 userBalance = ethicalMassToken.balanceOf(msg.sender);
        UD60x18 userMass = ud(userBalance * 1e18);
        require(userMass.gte(SOVEREIGN_THRESHOLD), "VortexOracle: Caller below Sovereign Threshold");

        // Format inputs into 60.18 fixed-point UD60x18 types
        UD60x18 proposalUD = ud(rawProposal * 1e18);
        UD60x18 confidenceUD = ud((rawConfidenceBasisPoints * 1e18) / 10000);

        round.responses.push(Response({
            participant: msg.sender,
            proposal: proposalUD,
            confidence: confidenceUD,
            ethicalMass: userMass
        }));

        hasParticipated[roundId][msg.sender] = true;
        emit ResponseSubmitted(roundId, msg.sender, rawProposal);

        // Auto-resolve if minimum participant threshold is met
        if (round.responses.length >= round.minParticipants) {
            _resolveConsensus(roundId);
        }
    }

    /**
     * @notice Internal resolution using logarithmic transformation for gas-optimized geometric mean:
     * ln(HarmonicCenter) = sum(Weight_i * ln(Proposal_i)) / sum(Weight_i)
     */
    function _resolveConsensus(bytes32 roundId) internal {
        ConsensusRound storage round = rounds[roundId];
        uint256 count = round.responses.length;
        
        UD60x18 weightedLogSum = ud(0);
        UD60x18 totalWeight = ud(0);

        // Calculate weighted geometric mean in log-space
        for (uint256 i = 0; i < count; i++) {
            Response memory res = round.responses[i];
            
            // Weight = EthicalMass * Confidence
            UD60x18 weight = res.ethicalMass.mul(res.confidence);
            
            if (weight.gt(ud(0)) && res.proposal.gt(ud(0))) {
                UD60x18 logProposal = res.proposal.ln();
                weightedLogSum = weightedLogSum.add(weight.mul(logProposal));
                totalWeight = totalWeight.add(weight);
            }
        }

        require(totalWeight.gt(ud(0)), "VortexOracle: Total weight is zero");

        // Invert log to acquire the exact weighted geometric mean
        UD60x18 logMean = weightedLogSum.div(totalWeight);
        round.harmonicCenter = logMean.exp();

        // Calculate system harmony coherence score: 1.0 - (WeightedAbsoluteDeviation / Mean)
        UD60x18 totalWeightedDeviation = ud(0);
        for (uint256 i = 0; i < count; i++) {
            Response memory res = round.responses[i];
            UD60x18 weight = res.ethicalMass.mul(res.confidence);
            
            UD60x18 diff = res.proposal.gte(round.harmonicCenter)
                ? res.proposal.sub(round.harmonicCenter)
                : round.harmonicCenter.sub(res.proposal);

            totalWeightedDeviation = totalWeightedDeviation.add(weight.mul(diff));
        }

        UD60x18 normalizedError = (totalWeightedDeviation.div(totalWeight)).div(round.harmonicCenter);
        
        // Ensure error does not underflow coherence calculation
        if (normalizedError.gte(ud(1e18))) {
            round.harmonyScore = ud(0);
        } else {
            round.harmonyScore = ud(1e18).sub(normalizedError);
        }

        round.resolved = true;
        
        emit ConsensusResolved(
            roundId,
            UD60x18.unwrap(round.harmonicCenter) / 1e18,
            UD60x18.unwrap(round.harmonyScore) / 1e15, // Output as basis points (0-1000)
            count
        );
    }

    // Two-Step Ownership Functions
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "VortexOracle: Zero address");
        pendingOwner = newOwner;
        emit OwnershipTransferStarted(owner, newOwner);
    }

    function acceptOwnership() external {
        require(msg.sender == pendingOwner, "VortexOracle: Caller not pending owner");
        emit OwnershipTransferred(owner, pendingOwner);
        owner = pendingOwner;
        pendingOwner = address(0);
    }
}