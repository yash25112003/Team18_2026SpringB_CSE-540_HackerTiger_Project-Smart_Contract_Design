// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IValidationLedger
 * @notice Interface for Hacker Tiger's on-chain audit and consensus layer.
 *
 * @dev This contract is intentionally designed as a draft smart contract for the
 *      CSE 540 milestone. The goal is to represent the proposed architecture in
 *      code through clear interfaces, data structures, and intended behaviors.
 *
 *      What belongs on-chain:
 *      - deployment validation session metadata
 *      - validator registration
 *      - validator votes
 *      - hashes/URIs of off-chain evidence
 *      - final verdicts
 *
 *      What remains off-chain:
 *      - AI agent execution
 *      - full compliance/security reports
 *      - repository cloning and deployment actions
 *      - health-check details and other large artifacts
 */
interface IValidationLedger {
    /**
     * @notice High-level state of a deployment validation session.
     * Pending  -> session is still collecting validator input
     * Approved -> session has met quorum and positive consensus
     * Rejected -> session has met quorum but failed consensus
     */
    enum SessionStatus {
        Pending,
        Approved,
        Rejected
    }

    /**
     * @notice High-level session record for a deployment validation request.
     *
     * @param sessionId Unique identifier of the validation session
     * @param repoName Name of the repository or project being validated
     * @param commitHash Source-control commit under review
     * @param artifactHash Hash of the deployment package or bundled evidence
     * @param metadataURI URI pointing to off-chain details (IPFS/backend/etc.)
     * @param proposer Address that created the validation session
     * @param approvals Number of approval votes submitted
     * @param rejections Number of rejection votes submitted
     * @param totalVotes Total number of votes submitted
     * @param createdAt Block timestamp when the session was created
     * @param status Current state of the session
     * @param finalized Whether the session is closed to further voting
     */
    struct ValidationSession {
        uint256 sessionId;
        string repoName;
        string commitHash;
        string artifactHash;
        string metadataURI;
        address proposer;
        uint256 approvals;
        uint256 rejections;
        uint256 totalVotes;
        uint256 createdAt;
        SessionStatus status;
        bool finalized;
    }

    /**
     * @notice Validator profile used for governance and traceability.
     *
     * @param isAuthorized Whether the address can participate in voting
     * @param role Human-readable validator role
     * @param weight Optional trust/governance weight for future enhancement
     */
    struct ValidatorProfile {
        bool isAuthorized;
        string role;
        uint256 weight;
    }

    event ValidatorRegistered(
        address indexed validator,
        string role,
        uint256 weight
    );

    event ValidatorRemoved(address indexed validator);

    event SessionCreated(
        uint256 indexed sessionId,
        string repoName,
        string commitHash,
        address indexed proposer
    );

    event VoteSubmitted(
        uint256 indexed sessionId,
        address indexed validator,
        bool approved,
        string evidenceHash
    );

    event SessionFinalized(
        uint256 indexed sessionId,
        SessionStatus status
    );

    function registerValidator(
        address validator,
        string calldata role,
        uint256 weight
    ) external;

    function removeValidator(address validator) external;

    function createSession(
        string calldata repoName,
        string calldata commitHash,
        string calldata artifactHash,
        string calldata metadataURI
    ) external returns (uint256);

    function submitVote(
        uint256 sessionId,
        bool approved,
        string calldata evidenceHash
    ) external;

    function finalizeSession(uint256 sessionId) external;

    function getSession(uint256 sessionId)
        external
        view
        returns (ValidationSession memory);

    function getValidator(address validator)
        external
        view
        returns (ValidatorProfile memory);

    function hasValidatorVoted(uint256 sessionId, address validator)
        external
        view
        returns (bool);

    function isValidator(address account) external view returns (bool);
}
