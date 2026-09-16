// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./ERC963.sol";
import "./libraries/MathUtils.sol";

// PRBMath Integration Recommendation (Next Phase Roadmap)
// To achieve precise 18-decimal fixed-point geometric means and reduce gas,
// replace manual weighted arithmetic with PRBMathUD60x18:
//   import {PRBMathUD60x18} from "@prb/math/src/PRBMathUD60x18.sol";
// Then use:
//   uint256 harmonic = PRBMathUD60x18.avg(...);
// This provides safer, more precise math for resonance-weighted consensus.

/**
 * @notice FIXED VERSION.
 *
 * Original bug: the contract computed a "weighted geometric mean" via
 *   weightedProduct = weightedProduct * (answer ** weight)
 *   harmonicCenter  = weightedProduct ** (1 / totalWeight)
 *
 * Two fatal problems:
 *   1. `answer ** weight` overflows uint256 almost immediately once `weight`
 *      exceeds single digits (weight here can be in the thousands), and
 *      Solidity >=0.8 reverts on `**` overflow -- so submitResponse() would
 *      revert as soon as the minimum participant count was reached.
 *   2. `1 / totalWeight` is integer division. For any totalWeight > 1 this
 *      truncates to 0, making the exponent 0 and the "geometric mean"
 *      collapse to 1 regardless of input -- so even *if* it didn't revert,
 *      the math was wrong.
 *
 * True fixed-point geometric means need a proper log/exp fixed-point library
 * (e.g. PRBMath). If you want a real geometric mean on-chain, import one of
 * those rather than hand-rolling `**`. Absent that dependency, this fix uses
 * a weighted ARITHMETIC mean instead, which is overflow-safe with plain
 * SafeMath/native 0.8 checks and gives directionally the same
 * "high-ethical-mass, high-confidence responses count more" property.
 */
contract VortexOracleFixed {
    using SafeMath for uint256;

    struct Response {
        address participant;
        uint256 answer;            // 0-10000 basis points
        uint256 confidence;        // 0-1000
        uint256 ethicalMass;
        bytes32 resonanceProof;
    }

    struct ConsensusRequest {
        bytes32 questionId;
        string question;
        uint256 minParticipants;
        uint256 consensusThreshold;   // harmony score threshold (e.g., 700-1000)
        uint256 deadline;
        address[] participants;
        Response[] responses;
        uint256 harmonyScore;
        uint256 harmonicCenter;       // now a plain uint256, not bytes32(uint256)
        bool resolved;
    }

    mapping(bytes32 => ConsensusRequest) public requests;
    mapping(address => uint256) public participantScores;

    ERC963 public identityRegistry;

    event ConsensusRequested(bytes32 indexed questionId, string question, uint256 minParticipants, uint256 deadline);
    event ResponseSubmitted(bytes32 indexed questionId, address participant, uint256 answer, uint256 confidence);
    event ConsensusReached(bytes32 indexed questionId, uint256 harmonicCenter, uint256 harmonyScore, uint256 participants);

    constructor(address _identityRegistry) {
        identityRegistry = ERC963(_identityRegistry);
    }

    function requestConsensus(
        string calldata question,
        uint256 minParticipants,
        uint256 consensusThreshold,
        uint256 duration
    ) external returns (bytes32 questionId) {
        require(minParticipants >= 3, "Minimum 3 participants");
        require(consensusThreshold >= 700, "Threshold too low");
        require(duration > 0, "Duration must be positive");

        questionId = keccak256(abi.encodePacked(question, block.timestamp, msg.sender));
        require(requests[questionId].deadline == 0, "Question id collision, retry");

        ConsensusRequest storage req = requests[questionId];
        req.questionId = questionId;
        req.question = question;
        req.minParticipants = minParticipants;
        req.consensusThreshold = consensusThreshold;
        req.deadline = block.timestamp + duration;

        emit ConsensusRequested(questionId, question, minParticipants, req.deadline);
    }

    function submitResponse(
        bytes32 questionId,
        uint256 answer,
        uint256 confidence,
        bytes32 resonanceProof
    ) external {
        ConsensusRequest storage req = requests[questionId];
        require(req.deadline != 0, "Question does not exist");
        require(block.timestamp <= req.deadline, "Deadline passed");
        require(!req.resolved, "Already resolved");
        require(answer <= 10000, "Answer out of range");
        require(confidence <= 1000, "Confidence out of range");

        (bool valid, uint256 mass,,) = identityRegistry.validateIdentity(msg.sender);
        require(valid && mass >= 6180, "Not sovereign");

        bool exists;
        for (uint i = 0; i < req.participants.length; i++) {
            if (req.participants[i] == msg.sender) { exists = true; break; }
        }
        require(!exists, "Already responded");
        req.participants.push(msg.sender);

        req.responses.push(Response(msg.sender, answer, confidence, mass, resonanceProof));
        emit ResponseSubmitted(questionId, msg.sender, answer, confidence);

        if (req.responses.length >= req.minParticipants) {
            _calculateConsensus(questionId);
        }
    }

    function _calculateConsensus(bytes32 questionId) internal {
        ConsensusRequest storage req = requests[questionId];
        uint256 n = req.responses.length;

        // Weighted ARITHMETIC mean: sum(answer * weight) / sum(weight).
        // (Future: replace with PRBMathUD60x18 for true geometric mean support
        //  and 18-decimal precision while keeping gas low.)
        // Overflow-safe: answer <= 10000, weight = ethicalMass*confidence/1000
        // so ethicalMass (<=10000) * confidence (<=1000) / 1000 <= 10000;
        // answer * weight <= 1e8, well within uint256 range even summed
        // across thousands of participants.
        uint256 weightedSum;
        uint256 totalWeight;
        for (uint i = 0; i < n; i++) {
            Response storage r = req.responses[i];
            uint256 weight = r.ethicalMass.mul(r.confidence).div(1000);
            weightedSum = weightedSum.add(r.answer.mul(weight));
            totalWeight = totalWeight.add(weight);
        }
        require(totalWeight > 0, "Zero total weight");

        uint256 harmonicCenter = weightedSum.div(totalWeight);
        req.harmonicCenter = harmonicCenter;

        // Harmony score: 1000 - normalized weighted deviation from the center.
        uint256 totalDeviation;
        uint256 maxPossibleDeviation;
        for (uint i = 0; i < n; i++) {
            Response storage r = req.responses[i];
            uint256 dev = MathUtils.absDiff(int256(r.answer), int256(harmonicCenter));
            totalDeviation = totalDeviation.add(dev.mul(r.ethicalMass));
            maxPossibleDeviation = maxPossibleDeviation.add(uint256(10000).mul(r.ethicalMass));
        }
        req.harmonyScore = maxPossibleDeviation == 0
            ? 1000
            : 1000 - totalDeviation.mul(1000).div(maxPossibleDeviation);
        req.resolved = true;

        for (uint i = 0; i < n; i++) {
            Response storage r = req.responses[i];
            uint256 dist = MathUtils.absDiff(int256(r.answer), int256(harmonicCenter));
            uint256 scoreIncrease = (1000 - dist.mul(1000).div(10000)).mul(req.harmonyScore).div(1000);
            participantScores[r.participant] += scoreIncrease;
        }

        emit ConsensusReached(questionId, harmonicCenter, req.harmonyScore, n);
    }
}
