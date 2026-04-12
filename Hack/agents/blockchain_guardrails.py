#!/usr/bin/env python3
"""
Blockchain Guardrails Framework
Mandatory security layer for all agents enforcing foundational blockchain principles.
"""

import json
import hashlib
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import os

class GuardrailViolationType(Enum):
    """Types of guardrail violations."""
    IMMUTABILITY_VIOLATION = "immutability_violation"
    CONSENSUS_VIOLATION = "consensus_violation"
    STAKE_VIOLATION = "stake_violation"
    AUDIT_VIOLATION = "audit_violation"
    SIGNATURE_VIOLATION = "signature_violation"
    TIMESTAMP_VIOLATION = "timestamp_violation"
    SEQUENCE_VIOLATION = "sequence_violation"
    MERKLE_VIOLATION = "merkle_violation"
    QUORUM_VIOLATION = "quorum_violation"
    POLICY_VIOLATION = "policy_violation"

@dataclass
class GuardrailViolation:
    """Represents a guardrail violation."""
    violation_type: GuardrailViolationType
    rule_section: str
    description: str
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    evidence: Dict[str, Any]
    timestamp: str
    agent_id: str

@dataclass
class GuardrailValidationResult:
    """Result of guardrail validation."""
    passed: bool
    violations: List[GuardrailViolation]
    validation_timestamp: str
    merkle_root: str
    signature_valid: bool
    consensus_met: bool
    stake_requirements_met: bool
    audit_integrity_verified: bool

class BlockchainGuardrails:
    """
    Mandatory blockchain guardrails framework.
    Enforces all foundational blockchain principles from the JSON specification.
    """
    
    def __init__(self, config_file: str = "json_file_gpt.json"):
        """Initialize guardrails with blockchain policies."""
        self.logger = logging.getLogger(__name__)
        self.policies = self._load_blockchain_policies(config_file)
        self.violations = []
        self.merkle_roots = {}
        
    def _load_blockchain_policies(self, config_file: str) -> Dict[str, Any]:
        """Load blockchain policies from JSON configuration."""
        try:
            # Always resolve path relative to this file
            base_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(base_dir, config_file)
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load blockchain policies: {e}")
            return {}
    
    def validate_immutability(self, data: Dict[str, Any], agent_id: str) -> GuardrailViolation:
        """Validate immutability requirements."""
        try:
            # Check for append-only ledger compliance
            if 'previous_hash' not in data:
                return GuardrailViolation(
                    violation_type=GuardrailViolationType.IMMUTABILITY_VIOLATION,
                    rule_section="Proof_of_Stake",
                    description="Missing previous hash for immutability chain",
                    severity="CRITICAL",
                    evidence={"missing_field": "previous_hash"},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    agent_id=agent_id
                )
            
            # Verify hash chain integrity
            if 'current_hash' in data:
                # Create a copy without current_hash for validation
                data_to_verify = data.copy()
                del data_to_verify['current_hash']
                expected_hash = self._calculate_hash(data_to_verify)
                
                if data['current_hash'] != expected_hash:
                    return GuardrailViolation(
                        violation_type=GuardrailViolationType.IMMUTABILITY_VIOLATION,
                        rule_section="Proof_of_Stake",
                        description="Hash chain integrity violation",
                        severity="CRITICAL",
                        evidence={
                            "expected_hash": expected_hash,
                            "actual_hash": data['current_hash']
                        },
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        agent_id=agent_id
                    )
            
            return None
            
        except Exception as e:
            return GuardrailViolation(
                violation_type=GuardrailViolationType.IMMUTABILITY_VIOLATION,
                rule_section="Proof_of_Stake",
                description=f"Immutability validation error: {str(e)}",
                severity="HIGH",
                evidence={"error": str(e)},
                timestamp=datetime.now(timezone.utc).isoformat(),
                agent_id=agent_id
            )
    
    def validate_consensus_requirements(self, agent_results: List[Dict], agent_id: str) -> GuardrailViolation:
        """Validate consensus requirements from blockchain rules."""
        try:
            # Check quorum threshold (default 2/3 supermajority)
            total_agents = len(agent_results)
            if total_agents == 0:
                return GuardrailViolation(
                    violation_type=GuardrailViolationType.CONSENSUS_VIOLATION,
                    rule_section="Blockchain_Validation_Rules",
                    description="No agents available for consensus",
                    severity="CRITICAL",
                    evidence={"total_agents": 0},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    agent_id=agent_id
                )
            
            # Check for minimum quorum (66% for standard operations)
            approve_count = len([r for r in agent_results if r.get('verdict') == 'APPROVE'])
            quorum_ratio = approve_count / total_agents if total_agents > 0 else 0
            
            if quorum_ratio < 0.66:
                return GuardrailViolation(
                    violation_type=GuardrailViolationType.QUORUM_VIOLATION,
                    rule_section="Blockchain_Validation_Rules",
                    description=f"Insufficient quorum: {quorum_ratio:.2f} < 0.66",
                    severity="CRITICAL",
                    evidence={
                        "quorum_ratio": quorum_ratio,
                        "approve_count": approve_count,
                        "total_agents": total_agents
                    },
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    agent_id=agent_id
                )
            
            return None
            
        except Exception as e:
            return GuardrailViolation(
                violation_type=GuardrailViolationType.CONSENSUS_VIOLATION,
                rule_section="Blockchain_Validation_Rules",
                description=f"Consensus validation error: {str(e)}",
                severity="HIGH",
                evidence={"error": str(e)},
                timestamp=datetime.now(timezone.utc).isoformat(),
                agent_id=agent_id
            )
    
    def validate_stake_requirements(self, agent_data: Dict[str, Any], agent_id: str) -> GuardrailViolation:
        """Validate stake and reputation requirements."""
        try:
            # Check stake requirements (0-1000 range)
            stake = agent_data.get('stake', 0)
            if not isinstance(stake, (int, float)) or stake < 0 or stake > 1000:
                return GuardrailViolation(
                    violation_type=GuardrailViolationType.STAKE_VIOLATION,
                    rule_section="Proof_of_Stake",
                    description=f"Invalid stake value: {stake} (must be 0-1000)",
                    severity="HIGH",
                    evidence={"stake": stake},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    agent_id=agent_id
                )
            
            # Check reputation requirements (0-100 range)
            reputation = agent_data.get('reputation', 0)
            if not isinstance(reputation, (int, float)) or reputation < 0 or reputation > 100:
                return GuardrailViolation(
                    violation_type=GuardrailViolationType.STAKE_VIOLATION,
                    rule_section="Proof_of_Stake",
                    description=f"Invalid reputation value: {reputation} (must be 0-100)",
                    severity="HIGH",
                    evidence={"reputation": reputation},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    agent_id=agent_id
                )
            
            # Check minimum stake for critical operations
            if agent_data.get('operation_type') == 'critical' and stake < 500:
                return GuardrailViolation(
                    violation_type=GuardrailViolationType.STAKE_VIOLATION,
                    rule_section="Proof_of_Stake",
                    description=f"Insufficient stake for critical operation: {stake} < 500",
                    severity="CRITICAL",
                    evidence={"stake": stake, "operation_type": "critical"},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    agent_id=agent_id
                )
            
            return None
            
        except Exception as e:
            return GuardrailViolation(
                violation_type=GuardrailViolationType.STAKE_VIOLATION,
                rule_section="Proof_of_Stake",
                description=f"Stake validation error: {str(e)}",
                severity="HIGH",
                evidence={"error": str(e)},
                timestamp=datetime.now(timezone.utc).isoformat(),
                agent_id=agent_id
            )
    
    def validate_audit_integrity(self, audit_data: Dict[str, Any], agent_id: str) -> GuardrailViolation:
        """Validate audit integrity requirements."""
        try:
            # Check for required audit fields
            required_fields = ['timestamp', 'agent_id', 'action', 'evidence_hash']
            missing_fields = [field for field in required_fields if field not in audit_data]
            
            if missing_fields:
                return GuardrailViolation(
                    violation_type=GuardrailViolationType.AUDIT_VIOLATION,
                    rule_section="Validator_Nodes",
                    description=f"Missing required audit fields: {missing_fields}",
                    severity="HIGH",
                    evidence={"missing_fields": missing_fields},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    agent_id=agent_id
                )
            
            # Verify evidence hash
            if 'evidence_hash' in audit_data:
                expected_hash = self._calculate_evidence_hash(audit_data)
                if audit_data['evidence_hash'] != expected_hash:
                    return GuardrailViolation(
                        violation_type=GuardrailViolationType.AUDIT_VIOLATION,
                        rule_section="Validator_Nodes",
                        description="Evidence hash mismatch",
                        severity="CRITICAL",
                        evidence={
                            "expected_hash": expected_hash,
                            "actual_hash": audit_data['evidence_hash']
                        },
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        agent_id=agent_id
                    )
            
            return None
            
        except Exception as e:
            return GuardrailViolation(
                violation_type=GuardrailViolationType.AUDIT_VIOLATION,
                rule_section="Validator_Nodes",
                description=f"Audit integrity validation error: {str(e)}",
                severity="HIGH",
                evidence={"error": str(e)},
                timestamp=datetime.now(timezone.utc).isoformat(),
                agent_id=agent_id
            )
    
    def validate_signature_requirements(self, signed_data: Dict[str, Any], agent_id: str) -> GuardrailViolation:
        """Validate signature requirements."""
        try:
            # Check for required signature fields
            if 'signature' not in signed_data:
                return GuardrailViolation(
                    violation_type=GuardrailViolationType.SIGNATURE_VIOLATION,
                    rule_section="Blockchain_Validation_Rules",
                    description="Missing signature for signed data",
                    severity="CRITICAL",
                    evidence={"missing_field": "signature"},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    agent_id=agent_id
                )
            
            # Check for nonce to prevent replay attacks
            if 'nonce' not in signed_data:
                return GuardrailViolation(
                    violation_type=GuardrailViolationType.SIGNATURE_VIOLATION,
                    rule_section="Blockchain_Validation_Rules",
                    description="Missing nonce for replay protection",
                    severity="HIGH",
                    evidence={"missing_field": "nonce"},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    agent_id=agent_id
                )
            
            # Verify signature format (basic check)
            signature = signed_data.get('signature', '')
            if not isinstance(signature, str) or len(signature) < 64:
                return GuardrailViolation(
                    violation_type=GuardrailViolationType.SIGNATURE_VIOLATION,
                    rule_section="Blockchain_Validation_Rules",
                    description="Invalid signature format",
                    severity="HIGH",
                    evidence={"signature_length": len(signature)},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    agent_id=agent_id
                )
            
            return None
            
        except Exception as e:
            return GuardrailViolation(
                violation_type=GuardrailViolationType.SIGNATURE_VIOLATION,
                rule_section="Blockchain_Validation_Rules",
                description=f"Signature validation error: {str(e)}",
                severity="HIGH",
                evidence={"error": str(e)},
                timestamp=datetime.now(timezone.utc).isoformat(),
                agent_id=agent_id
            )
    
    def validate_timestamp_requirements(self, timestamp_data: Dict[str, Any], agent_id: str) -> GuardrailViolation:
        """Validate timestamp requirements."""
        try:
            # Check timestamp format and drift tolerance
            timestamp = timestamp_data.get('timestamp')
            if not timestamp:
                return GuardrailViolation(
                    violation_type=GuardrailViolationType.TIMESTAMP_VIOLATION,
                    rule_section="Blockchain_Validation_Rules",
                    description="Missing timestamp",
                    severity="HIGH",
                    evidence={"missing_field": "timestamp"},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    agent_id=agent_id
                )
            
            # Parse timestamp and check drift (default ±5 seconds)
            try:
                if isinstance(timestamp, str):
                    ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    ts = timestamp
                
                now = datetime.now(timezone.utc)
                drift_seconds = abs((now - ts).total_seconds())
                
                if drift_seconds > 5:  # 5 second tolerance
                    return GuardrailViolation(
                        violation_type=GuardrailViolationType.TIMESTAMP_VIOLATION,
                        rule_section="Blockchain_Validation_Rules",
                        description=f"Timestamp drift exceeds tolerance: {drift_seconds:.2f}s > 5s",
                        severity="MEDIUM",
                        evidence={
                            "drift_seconds": drift_seconds,
                            "timestamp": timestamp,
                            "current_time": now.isoformat()
                        },
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        agent_id=agent_id
                    )
                
            except ValueError as e:
                return GuardrailViolation(
                    violation_type=GuardrailViolationType.TIMESTAMP_VIOLATION,
                    rule_section="Blockchain_Validation_Rules",
                    description=f"Invalid timestamp format: {str(e)}",
                    severity="HIGH",
                    evidence={"timestamp": timestamp, "error": str(e)},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    agent_id=agent_id
                )
            
            return None
            
        except Exception as e:
            return GuardrailViolation(
                violation_type=GuardrailViolationType.TIMESTAMP_VIOLATION,
                rule_section="Blockchain_Validation_Rules",
                description=f"Timestamp validation error: {str(e)}",
                severity="HIGH",
                evidence={"error": str(e)},
                timestamp=datetime.now(timezone.utc).isoformat(),
                agent_id=agent_id
            )
    
    def validate_merkle_proofs(self, merkle_data: Dict[str, Any], agent_id: str) -> GuardrailViolation:
        """Validate Merkle proof requirements."""
        try:
            # Check for Merkle root
            if 'merkle_root' not in merkle_data:
                return GuardrailViolation(
                    violation_type=GuardrailViolationType.MERKLE_VIOLATION,
                    rule_section="Attestations_and_Block_Proposal",
                    description="Missing Merkle root for evidence verification",
                    severity="HIGH",
                    evidence={"missing_field": "merkle_root"},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    agent_id=agent_id
                )
            
            # Verify Merkle root format
            merkle_root = merkle_data.get('merkle_root', '')
            if not isinstance(merkle_root, str) or len(merkle_root) != 64:
                return GuardrailViolation(
                    violation_type=GuardrailViolationType.MERKLE_VIOLATION,
                    rule_section="Attestations_and_Block_Proposal",
                    description="Invalid Merkle root format",
                    severity="HIGH",
                    evidence={"merkle_root_length": len(merkle_root)},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    agent_id=agent_id
                )
            
            return None
            
        except Exception as e:
            return GuardrailViolation(
                violation_type=GuardrailViolationType.MERKLE_VIOLATION,
                rule_section="Attestations_and_Block_Proposal",
                description=f"Merkle proof validation error: {str(e)}",
                severity="HIGH",
                evidence={"error": str(e)},
                timestamp=datetime.now(timezone.utc).isoformat(),
                agent_id=agent_id
            )
    
    def validate_policy_compliance(self, policy_data: Dict[str, Any], agent_id: str) -> GuardrailViolation:
        """Validate policy compliance requirements."""
        try:
            # Check for required policy fields
            required_policy_fields = ['version', 'effective_date', 'signature']
            missing_fields = [field for field in required_policy_fields if field not in policy_data]
            
            if missing_fields:
                return GuardrailViolation(
                    violation_type=GuardrailViolationType.POLICY_VIOLATION,
                    rule_section="Blockchain_Validation_Rules",
                    description=f"Missing required policy fields: {missing_fields}",
                    severity="HIGH",
                    evidence={"missing_fields": missing_fields},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    agent_id=agent_id
                )
            
            # Check policy version
            version = policy_data.get('version')
            if not version or not isinstance(version, str):
                return GuardrailViolation(
                    violation_type=GuardrailViolationType.POLICY_VIOLATION,
                    rule_section="Blockchain_Validation_Rules",
                    description="Invalid policy version",
                    severity="HIGH",
                    evidence={"version": version},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    agent_id=agent_id
                )
            
            return None
            
        except Exception as e:
            return GuardrailViolation(
                violation_type=GuardrailViolationType.POLICY_VIOLATION,
                rule_section="Blockchain_Validation_Rules",
                description=f"Policy compliance validation error: {str(e)}",
                severity="HIGH",
                evidence={"error": str(e)},
                timestamp=datetime.now(timezone.utc).isoformat(),
                agent_id=agent_id
            )
    
    def _calculate_hash(self, data: Dict[str, Any]) -> str:
        """Calculate SHA256 hash of data."""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()
    
    def _calculate_evidence_hash(self, audit_data: Dict[str, Any]) -> str:
        """Calculate evidence hash for audit data."""
        evidence_fields = ['timestamp', 'agent_id', 'action', 'evidence']
        evidence_data = {k: v for k, v in audit_data.items() if k in evidence_fields}
        return self._calculate_hash(evidence_data)
    
    def validate_all_guardrails(self, agent_data: Dict[str, Any], agent_id: str) -> GuardrailValidationResult:
        """
        Validate all blockchain guardrails for an agent.
        This is the main entry point for guardrail validation.
        """
        violations = []
        validation_timestamp = datetime.now(timezone.utc).isoformat()
        
        # Validate immutability
        immutability_violation = self.validate_immutability(agent_data, agent_id)
        if immutability_violation:
            violations.append(immutability_violation)
        
        # Validate stake requirements
        stake_violation = self.validate_stake_requirements(agent_data, agent_id)
        if stake_violation:
            violations.append(stake_violation)
        
        # Validate audit integrity
        audit_violation = self.validate_audit_integrity(agent_data, agent_id)
        if audit_violation:
            violations.append(audit_violation)
        
        # Validate signature requirements
        signature_violation = self.validate_signature_requirements(agent_data, agent_id)
        if signature_violation:
            violations.append(signature_violation)
        
        # Validate timestamp requirements
        timestamp_violation = self.validate_timestamp_requirements(agent_data, agent_id)
        if timestamp_violation:
            violations.append(timestamp_violation)
        
        # Validate Merkle proofs
        merkle_violation = self.validate_merkle_proofs(agent_data, agent_id)
        if merkle_violation:
            violations.append(merkle_violation)
        
        # Validate policy compliance
        policy_violation = self.validate_policy_compliance(agent_data, agent_id)
        if policy_violation:
            violations.append(policy_violation)
        
        # Calculate Merkle root for validation result
        merkle_root = self._calculate_hash({
            "agent_id": agent_id,
            "timestamp": validation_timestamp,
            "violations": [asdict(v) for v in violations]
        })
        
        # Determine if validation passed
        passed = len(violations) == 0
        
        # Check specific requirements
        signature_valid = not any(v.violation_type == GuardrailViolationType.SIGNATURE_VIOLATION for v in violations)
        consensus_met = not any(v.violation_type == GuardrailViolationType.CONSENSUS_VIOLATION for v in violations)
        stake_requirements_met = not any(v.violation_type == GuardrailViolationType.STAKE_VIOLATION for v in violations)
        audit_integrity_verified = not any(v.violation_type == GuardrailViolationType.AUDIT_VIOLATION for v in violations)
        
        return GuardrailValidationResult(
            passed=passed,
            violations=violations,
            validation_timestamp=validation_timestamp,
            merkle_root=merkle_root,
            signature_valid=signature_valid,
            consensus_met=consensus_met,
            stake_requirements_met=stake_requirements_met,
            audit_integrity_verified=audit_integrity_verified
        )
    
    def get_guardrail_summary(self, validation_result: GuardrailValidationResult) -> Dict[str, Any]:
        """Get a summary of guardrail validation results."""
        return {
            "guardrail_validation": {
                "passed": validation_result.passed,
                "violations_count": len(validation_result.violations),
                "critical_violations": len([v for v in validation_result.violations if v.severity == "CRITICAL"]),
                "high_violations": len([v for v in validation_result.violations if v.severity == "HIGH"]),
                "violations": [
                    {
                        "type": v.violation_type.value,
                        "rule_section": v.rule_section,
                        "description": v.description,
                        "severity": v.severity,
                        "evidence": v.evidence
                    } for v in validation_result.violations
                ],
                "validation_metrics": {
                    "signature_valid": validation_result.signature_valid,
                    "consensus_met": validation_result.consensus_met,
                    "stake_requirements_met": validation_result.stake_requirements_met,
                    "audit_integrity_verified": validation_result.audit_integrity_verified
                },
                "merkle_root": validation_result.merkle_root,
                "validation_timestamp": validation_result.validation_timestamp
            }
        }
