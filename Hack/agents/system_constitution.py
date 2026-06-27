"""
System Constitution: Universal Rules & Policies
Implements immutable, non-negotiable principles for the multi-agent validation system.
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class VerdictType(Enum):
    """Final verdict types for deployment validation."""
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ISOLATE = "ISOLATE"


class ThreatLevel(Enum):
    """Threat severity levels following Microsoft Bug Bar methodology."""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    INFO = 1


@dataclass
class SystemConstitution:
    """
    Immutable system constitution defining core principles and policies.
    All rules are non-negotiable and enforced across all agents.
    """
    
    # Core Principles
    IMMUTABILITY_ENABLED: bool = True
    ZERO_TRUST_ENABLED: bool = True
    PARALLEL_VALIDATION_ENABLED: bool = True
    TRAP_AND_ISOLATE_ENABLED: bool = True
    
    # Consensus Configuration
    CONSENSUS_QUORUM_THRESHOLD: float = 0.75
    MINIMUM_AGENTS_FOR_QUORUM: int = 3
    CRITICAL_THREAT_THRESHOLD: int = ThreatLevel.HIGH.value
    
    # Security Policies
    HASH_ALGORITHM: str = "SHA256"
    AUDIT_LOG_RETENTION_DAYS: int = 365
    SESSION_TIMEOUT_SECONDS: int = 300
    
    # Agent Behavior Rules
    AGENT_EXPLAINABILITY_REQUIRED: bool = True
    THREAT_MODELING_MANDATORY: bool = True
    PRIVACY_SCANNING_MANDATORY: bool = True
    DEPENDENCY_AUDIT_MANDATORY: bool = True
    
    # Red Team & Adversarial Testing
    RED_TEAM_TESTING_ENABLED: bool = True
    ADVERSARIAL_ANALYSIS_ENABLED: bool = True
    ANOMALY_DETECTION_ENABLED: bool = True
    
    # Compliance Requirements
    GDPR_COMPLIANCE_REQUIRED: bool = True
    SOC2_COMPLIANCE_REQUIRED: bool = True
    AI_ETHICS_REVIEW_REQUIRED: bool = True
    
    def __post_init__(self):
        """Validate constitution parameters after initialization."""
        if not 0.0 <= self.CONSENSUS_QUORUM_THRESHOLD <= 1.0:
            raise ValueError("Consensus quorum threshold must be between 0.0 and 1.0")
        
        if self.MINIMUM_AGENTS_FOR_QUORUM < 1:
            raise ValueError("Minimum agents for quorum must be at least 1")
    
    def get_hash(self) -> str:
        """Generate immutable hash of the constitution."""
        constitution_data = {
            "immutability": self.IMMUTABILITY_ENABLED,
            "zero_trust": self.ZERO_TRUST_ENABLED,
            "parallel_validation": self.PARALLEL_VALIDATION_ENABLED,
            "trap_and_isolate": self.TRAP_AND_ISOLATE_ENABLED,
            "quorum_threshold": self.CONSENSUS_QUORUM_THRESHOLD,
            "minimum_agents": self.MINIMUM_AGENTS_FOR_QUORUM,
            "critical_threat_threshold": self.CRITICAL_THREAT_THRESHOLD,
            "hash_algorithm": self.HASH_ALGORITHM,
            "retention_days": self.AUDIT_LOG_RETENTION_DAYS,
            "session_timeout": self.SESSION_TIMEOUT_SECONDS
        }
        
        constitution_json = json.dumps(constitution_data, sort_keys=True)
        return hashlib.sha256(constitution_json.encode()).hexdigest()


class ImmutableRecord:
    """
    Base class for immutable records that cannot be modified once created.
    All audit logs and validation results inherit from this.
    """
    
    def __init__(self, data: Dict[str, Any], session_id: str):
        self.data = data
        self.session_id = session_id
        self.timestamp = datetime.utcnow().isoformat()
        self.hash = self._generate_hash()
        self._frozen = True
    
    def _generate_hash(self) -> str:
        """Generate SHA256 hash of the record."""
        record_data = {
            "data": self.data,
            "session_id": self.session_id,
            "timestamp": self.timestamp
        }
        record_json = json.dumps(record_data, sort_keys=True)
        return hashlib.sha256(record_json.encode()).hexdigest()
    
    def __setattr__(self, name, value):
        """Prevent modification of frozen records."""
        if hasattr(self, '_frozen') and self._frozen:
            raise AttributeError(f"Cannot modify immutable record: {name}")
        super().__setattr__(name, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary for serialization."""
        return {
            "data": self.data,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "hash": self.hash
        }


class AuditLog(ImmutableRecord):
    """Immutable audit log entry for all system activities."""
    
    def __init__(self, action: str, agent_name: str, result: Dict[str, Any], 
                 session_id: str, metadata: Optional[Dict[str, Any]] = None):
        data = {
            "action": action,
            "agent_name": agent_name,
            "result": result,
            "metadata": metadata or {}
        }
        super().__init__(data, session_id)


class ValidationResult(ImmutableRecord):
    """Immutable validation result from an agent."""
    
    def __init__(self, agent_name: str, verdict: str, confidence: float,
                 details: Dict[str, Any], session_id: str, 
                 threat_level: Optional[ThreatLevel] = None):
        data = {
            "agent_name": agent_name,
            "verdict": verdict,
            "confidence": confidence,
            "details": details,
            "threat_level": threat_level.value if threat_level else None
        }
        super().__init__(data, session_id)


class ConsensusResult(ImmutableRecord):
    """Immutable final consensus result for a deployment."""
    
    def __init__(self, final_verdict: VerdictType, agent_results: List[ValidationResult],
                 consensus_score: float, session_id: str, 
                 critical_findings: List[Dict[str, Any]] = None):
        data = {
            "final_verdict": final_verdict.value,
            "agent_results": [result.to_dict() for result in agent_results],
            "consensus_score": consensus_score,
            "critical_findings": critical_findings or [],
            "total_agents": len(agent_results),
            "approval_count": sum(1 for r in agent_results if r.data["verdict"] == "APPROVE"),
            "rejection_count": sum(1 for r in agent_results if r.data["verdict"] == "REJECT")
        }
        super().__init__(data, session_id)


class ThreatModel:
    """Microsoft-inspired threat modeling framework."""
    
    THREAT_CATEGORIES = {
        "EVASION": "Adversarial evasion attacks",
        "MISUSE": "Malicious misuse of AI systems", 
        "ADVERSARIAL_HARM": "Adversarial examples causing harm",
        "DATA_POISONING": "Training data manipulation",
        "MODEL_EXTRACTION": "Model architecture/theft",
        "PRIVACY_ATTACKS": "Membership inference, data extraction",
        "PROMPT_INJECTION": "LLM prompt manipulation",
        "BACKDOOR_ATTACKS": "Hidden malicious functionality"
    }
    
    ATTACKER_PROFILES = {
        "SCRIPT_KIDDIE": {"skill": 1, "resources": 1, "motivation": 2},
        "HACKTIVIST": {"skill": 3, "resources": 2, "motivation": 4},
        "CRIMINAL": {"skill": 4, "resources": 3, "motivation": 5},
        "NATION_STATE": {"skill": 5, "resources": 5, "motivation": 5},
        "INSIDER": {"skill": 4, "resources": 4, "motivation": 3}
    }
    
    @classmethod
    def assess_threat_landscape(cls, deployment_context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess threat landscape for a deployment."""
        threats = []
        
        # Analyze deployment characteristics
        if deployment_context.get("ai_model", False):
            threats.extend(["EVASION", "MISUSE", "ADVERSARIAL_HARM", "PROMPT_INJECTION"])
        
        if deployment_context.get("sensitive_data", False):
            threats.extend(["PRIVACY_ATTACKS", "DATA_POISONING"])
        
        if deployment_context.get("external_api", False):
            threats.extend(["PROMPT_INJECTION", "MISUSE"])
        
        # Calculate risk score
        risk_score = len(threats) * 2  # Base risk
        if deployment_context.get("public_facing", False):
            risk_score += 3
        
        return {
            "applicable_threats": threats,
            "risk_score": min(risk_score, 10),  # Cap at 10
            "recommended_controls": cls._get_recommended_controls(threats)
        }
    
    @classmethod
    def _get_recommended_controls(cls, threats: List[str]) -> List[str]:
        """Get recommended security controls for identified threats."""
        controls = []
        
        if "EVASION" in threats:
            controls.extend(["Adversarial training", "Input validation", "Anomaly detection"])
        
        if "MISUSE" in threats:
            controls.extend(["Rate limiting", "Content filtering", "User authentication"])
        
        if "PRIVACY_ATTACKS" in threats:
            controls.extend(["Differential privacy", "Data anonymization", "Access controls"])
        
        if "PROMPT_INJECTION" in threats:
            controls.extend(["Input sanitization", "Prompt engineering", "Output filtering"])
        
        return controls


# Global constitution instance
CONSTITUTION = SystemConstitution()

# Export key classes and constants
__all__ = [
    'SystemConstitution', 'CONSTITUTION', 'ImmutableRecord', 'AuditLog', 
    'ValidationResult', 'ConsensusResult', 'VerdictType', 'ThreatLevel', 'ThreatModel'
]
