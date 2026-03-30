// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./IValidationLedger.sol";

/**
 * @title DeploymentValidationLedger
 * @notice Draft implementation of the Hacker Tiger on-chain audit ledger.
 *
 * @dev Design intent:
 *      This contract models the blockchain-backed portion of the proposed
 *      Hacker Tiger architecture. The off-chain system performs AI-driven
 *      validation, threat analysis, compliance checks, and deployment handling.
 *      This contract stores only the minimum governance and audit data needed
 *      for transparency, integrity, and traceability.
 *
 *      Core responsibilities:
 *      1. Register trusted validators
 *      2. Create deployment validation sessions
 *      3. Record validator votes and evidence hashes
 *      4. Finalize verdicts after quorum
 *      5. Emit events for immutable audit trails
 *
 *      Important academic note:
 *      This is a draft smart contract design meant to demonstrate structure,
 *      interfaces, and intended behavior for the milestone. It is not trying
 *      to implement the entire production deployment pipeline on-chain.
 */
contract DeploymentValidationLedger is IValidationLedger {
    /// @notice Owner/admin of the contract, responsible for validator governance.
    address public owner;

    /// @notice Minimum number of votes required before finalization is allowed.
    uint256 public quorumThreshold;

    /// @notice Incrementing counter used to assign unique session IDs.
    uint256 public nextSessionId;

    /// @dev Stores validator profiles.
    mapping(address => ValidatorProfile) private validators;

    /// @dev Stores validation sessions by ID.
    mapping(uint256 => ValidationSession) private sessions;

    /// @dev Tracks whether a validator has already voted in a given session.
    mapping(uint256 => mapping(address => bool)) private voted;

    /// @dev Stores a validator's evidence hash for each session.
    mapping(uint256 => mapping(address => string)) private evidenceHashes;

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    modifier onlyValidator() {
        require(validators[msg.sender].isAuthorized, "Caller is not a validator");
        _;
    }

    /**
     * @param _quorumThreshold The minimum number of validator votes required
     *                         before a session can be finalized.
     */
    constructor(uint256 _quorumThreshold) {
        require(_quorumThreshold > 0, "Quorum must be greater than zero");

        owner = msg.sender;
        quorumThreshold = _quorumThreshold;
        nextSessionId = 1;
    }

    /**
     * @notice Registers a validator address that can participate in consensus.
     *
     * @dev In the broader Hacker Tiger design, validators may correspond to
     *      trusted governance roles or wallets representing specialized
     *      validation agents. A weight field is included for future weighted
     *      consensus expansion, even though the current draft uses simple
     *      majority logic.
     */
    function registerValidator(
        address validator,
        string calldata role,
        uint256 weight
    ) external override onlyOwner {
        require(validator != address(0), "Invalid validator address");
        require(bytes(role).length > 0, "Role cannot be empty");
        require(weight > 0, "Weight must be greater than zero");

        validators[validator] = ValidatorProfile({
            isAuthorized: true,
            role: role,
            weight: weight
        });

        emit ValidatorRegistered(validator, role, weight);
    }

    /**
     * @notice Removes a validator from the authorized validator set.
     *
     * @dev This affects future voting rights only. Historical votes and events
     *      remain on-chain for auditability.
     */
    function removeValidator(address validator) external override onlyOwner {
        require(validators[validator].isAuthorized, "Validator not found");

        delete validators[validator];
        emit ValidatorRemoved(validator);
    }

    /**
     * @notice Creates a new deployment validation session.
     *
     * @param repoName Name of the repository or project under review
     * @param commitHash Commit hash associated with the proposed deployment
     * @param artifactHash Hash of the deployment artifact or report bundle
     * @param metadataURI URI to off-chain metadata or evidence references
     *
     * @return sessionId Newly assigned session identifier
     *
     * @dev Only hashes/URIs are stored on-chain because complete AI reports,
     *      scan outputs, and deployment artifacts are too large and expensive
     *      to store directly in smart contract state.
     */
    function createSession(
        string calldata repoName,
        string calldata commitHash,
        string calldata artifactHash,
        string calldata metadataURI
    ) external override returns (uint256 sessionId) {
        require(bytes(repoName).length > 0, "Repository name required");
        require(bytes(commitHash).length > 0, "Commit hash required");
        require(bytes(artifactHash).length > 0, "Artifact hash required");

        sessionId = nextSessionId;
        nextSessionId += 1;

        sessions[sessionId] = ValidationSession({
            sessionId: sessionId,
            repoName: repoName,
            commitHash: commitHash,
            artifactHash: artifactHash,
            metadataURI: metadataURI,
            proposer: msg.sender,
            approvals: 0,
            rejections: 0,
            totalVotes: 0,
            createdAt: block.timestamp,
            status: SessionStatus.Pending,
            finalized: false
        });

        emit SessionCreated(sessionId, repoName, commitHash, msg.sender);
    }

    /**
     * @notice Submits a validator vote for a session.
     *
     * @param sessionId The validation session being voted on
     * @param approved True for approve, false for reject
     * @param evidenceHash Hash or content-addressed reference to the validator's
     *                     off-chain evidence/report
     *
     * @dev Each validator can vote only once per session. This prevents
     *      double-voting and preserves the integrity of the consensus process.
     */
    function submitVote(
        uint256 sessionId,
        bool approved,
        string calldata evidenceHash
    ) external override onlyValidator {
        ValidationSession storage session = sessions[sessionId];

        require(session.sessionId != 0, "Session does not exist");
        require(!session.finalized, "Session already finalized");
        require(!voted[sessionId][msg.sender], "Validator already voted");
        require(bytes(evidenceHash).length > 0, "Evidence hash required");

        voted[sessionId][msg.sender] = true;
        evidenceHashes[sessionId][msg.sender] = evidenceHash;
        session.totalVotes += 1;

        if (approved) {
            session.approvals += 1;
        } else {
            session.rejections += 1;
        }

        emit VoteSubmitted(sessionId, msg.sender, approved, evidenceHash);
    }

    /**
     * @notice Finalizes a validation session after quorum is reached.
     *
     * @dev Current draft finalization rule:
     *      - session must exist
     *      - session must not already be finalized
     *      - totalVotes must be >= quorumThreshold
     *      - approvals > rejections => Approved
     *      - otherwise => Rejected
     *
     *      This simple rule is appropriate for a design draft. In future phases,
     *      the project can upgrade to weighted voting or role-aware consensus.
     */
    function finalizeSession(uint256 sessionId) external override {
        ValidationSession storage session = sessions[sessionId];

        require(session.sessionId != 0, "Session does not exist");
        require(!session.finalized, "Session already finalized");
        require(session.totalVotes >= quorumThreshold, "Quorum not reached");

        if (session.approvals > session.rejections) {
            session.status = SessionStatus.Approved;
        } else {
            session.status = SessionStatus.Rejected;
        }

        session.finalized = true;

        emit SessionFinalized(sessionId, session.status);
    }

    /**
     * @notice Returns a session record for inspection by UI/backend layers.
     */
    function getSession(uint256 sessionId)
        external
        view
        override
        returns (ValidationSession memory)
    {
        require(sessions[sessionId].sessionId != 0, "Session does not exist");
        return sessions[sessionId];
    }

    /**
     * @notice Returns validator metadata for a given address.
     */
    function getValidator(address validator)
        external
        view
        override
        returns (ValidatorProfile memory)
    {
        require(validators[validator].isAuthorized, "Validator not found");
        return validators[validator];
    }

    /**
     * @notice Indicates whether a validator has already voted in a session.
     */
    function hasValidatorVoted(uint256 sessionId, address validator)
        external
        view
        override
        returns (bool)
    {
        return voted[sessionId][validator];
    }

    /**
     * @notice Returns true if the address is an authorized validator.
     */
    function isValidator(address account)
        external
        view
        override
        returns (bool)
    {
        return validators[account].isAuthorized;
    }

    /**
     * @notice Allows the owner to update quorum for future governance needs.
     *
     * @dev This helper is useful for iterative academic development and
     *      evolving validator participation.
     */
    function updateQuorumThreshold(uint256 newThreshold) external onlyOwner {
        require(newThreshold > 0, "Quorum must be greater than zero");
        quorumThreshold = newThreshold;
    }

    /**
     * @notice Transfers contract ownership to another administrator address.
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid owner address");
        owner = newOwner;
    }
}
