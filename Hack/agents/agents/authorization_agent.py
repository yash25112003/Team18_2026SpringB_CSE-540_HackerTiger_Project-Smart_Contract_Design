"""
Authorization Agent (Auth-Warden) - Enforces role-based access and verifies identity.
Given commit hash and author metadata, verifies authorization and access compliance.
"""

import json
import hashlib
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from .base_agent import ValidatorAgent, AgentResult, AgentStatus
except ImportError:
    # For standalone execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agents.base_agent import ValidatorAgent, AgentResult, AgentStatus
try:
    from ..utils.gemini_api import GeminiResponse
except ImportError:
    # For standalone execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.gemini_api import GeminiResponse
try:
    from ..system_constitution import ThreatLevel, CONSTITUTION
except ImportError:
    # For standalone execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from system_constitution import ThreatLevel, CONSTITUTION


class AccessLevel(Enum):
    """Access levels for authorization."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    OWNER = "owner"


class AuthorizationStatus(Enum):
    """Authorization status enumeration."""
    AUTHORIZED = "authorized"
    UNAUTHORIZED = "unauthorized"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


@dataclass
class AuthorizationCheck:
    """Structured authorization check result."""
    check_type: str
    status: AuthorizationStatus
    confidence: float
    description: str
    evidence: List[str]
    risk_factors: List[str]
    recommendations: List[str]


@dataclass
class AuthorizationReport:
    """Comprehensive authorization validation report."""
    total_checks: int
    authorized_checks: int
    unauthorized_checks: int
    partial_checks: int
    authorization_score: float
    checks: List[AuthorizationCheck]
    recommendations: List[str]


class AuthorizationAgent(ValidatorAgent):
    """
    Auth-Warden: Authorization validation agent for role-based access control.
    Verifies identity, permissions, and access compliance for deployments.
    """
    
    def __init__(self, gemini_api, audit_logger, session, config=None):
        super().__init__("Auth-Warden", gemini_api, audit_logger, session, config)
        
        # Authorization patterns
        self.authorization_patterns = {
            "commit_signature": r"-----BEGIN PGP SIGNATURE-----",
            "author_email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "commit_hash": r"^[a-f0-9]{40}$",
            "branch_protection": r"main|master|develop",
            "approval_required": r"approved|reviewed|verified"
        }
        
        # Role-based access control (RBAC) mapping
        self.rbac_mapping = {
            "developer": {"read": True, "write": True, "admin": False, "owner": False},
            "reviewer": {"read": True, "write": False, "admin": False, "owner": False},
            "admin": {"read": True, "write": True, "admin": True, "owner": False},
            "owner": {"read": True, "write": True, "admin": True, "owner": True}
        }
        
        # Security requirements
        self.security_requirements = {
            "commit_signing": True,
            "multi_factor_auth": True,
            "approval_workflow": True,
            "branch_protection": True,
            "access_logging": True
        }
    
    def get_prompt_template(self) -> str:
        """Get the authorization validation prompt template."""
        return """
You are Auth-Warden, an authorization validation agent specializing in role-based access control and identity verification. Your mission is to verify authorization and access compliance for deployments based on commit hash, author metadata, and access controls.

## Analysis Context:
- Commit Hash: {commit_hash}
- Author Metadata: {author_metadata}
- Access Controls: {access_controls}
- Deployment Context: {deployment_context}
- Security Requirements: {security_requirements}

## Your Authorization Framework:

### 1. Identity Verification
- **Commit Signing**: Verify GPG signatures and commit authenticity
- **Author Authentication**: Validate author identity and credentials
- **Multi-Factor Authentication**: Check for MFA requirements
- **Access History**: Review previous access patterns and behavior

### 2. Permission Validation
- **Role-Based Access**: Verify user roles and permissions
- **Resource Access**: Check access to specific resources and data
- **Operation Permissions**: Validate read, write, admin, owner permissions
- **Temporal Access**: Check time-based access restrictions

### 3. Authorization Checks
- **Commit Authorization**: Verify commit permissions and approvals
- **Deployment Authorization**: Check deployment permissions
- **Resource Authorization**: Validate resource access rights
- **Administrative Authorization**: Check administrative privileges

### 4. Security Controls
- **Access Logging**: Verify comprehensive access logging
- **Audit Trails**: Check audit trail completeness
- **Session Management**: Validate session controls and timeouts
- **Privilege Escalation**: Check for unauthorized privilege escalation

### 5. Compliance Validation
- **Principle of Least Privilege**: Verify minimal necessary permissions
- **Separation of Duties**: Check for conflicting roles
- **Access Reviews**: Validate regular access reviews
- **Offboarding**: Check for proper access revocation

## Output Format:
Provide a comprehensive authorization analysis in the following JSON structure:

```json
{{
    "authorization_report": {{
        "total_checks": integer,
        "authorized_checks": integer,
        "unauthorized_checks": integer,
        "partial_checks": integer,
        "authorization_score": float (0.0-1.0)
    }},
    "checks": [
        {{
            "check_type": "identity_verification|permission_validation|authorization_check|security_control|compliance_validation",
            "status": "authorized|unauthorized|partial|unknown",
            "confidence": float (0.0-1.0),
            "description": "Detailed authorization assessment",
            "evidence": ["evidence1", "evidence2"],
            "risk_factors": ["factor1", "factor2"],
            "recommendations": ["recommendation1", "recommendation2"]
        }}
    ],
    "recommendations": [
        "Priority authorization recommendations"
    ],
    "authorization_summary": {{
        "overall_status": "authorized|unauthorized|partial",
        "critical_issues": integer,
        "security_violations": integer,
        "access_gaps": ["gap1", "gap2"],
        "next_steps": ["step1", "step2"]
    }}
}}
```

## Authorization Guidelines:
1. **Be thorough** - Check all authorization aspects
2. **Be specific** - Provide detailed evidence and reasoning
3. **Prioritize security** - Focus on security-critical authorization issues
4. **Consider context** - Authorization varies by system and role
5. **Provide evidence** - Support findings with specific data points
6. **Suggest improvements** - Always recommend authorization enhancements

Analyze the provided deployment context for authorization and access compliance.
"""
    
    async def validate(self, deployment_context: Dict[str, Any]) -> AgentResult:
        """
        Perform comprehensive authorization validation.
        
        Args:
            deployment_context: Deployment context to analyze
            
        Returns:
            AgentResult: Authorization validation result
        """
        try:
            # Prepare analysis context
            analysis_context = self._prepare_analysis_context(deployment_context)
            
            # Generate authorization validation prompt
            prompt = self.get_prompt_template().format(**analysis_context)
            
            # Call Gemini for analysis
            response = await self._call_gemini(prompt)
            
            # Parse and validate response
            result = self.parse_response(response)
            
            # Perform additional authorization checks
            additional_checks = self._perform_additional_authorization_checks(deployment_context)
            
            # Merge results
            if additional_checks:
                result.details["additional_authorization_checks"] = additional_checks
            
            # Determine threat level
            result.threat_level = self._determine_threat_level(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Authorization validation failed: {e}")
            return AgentResult(
                agent_name=self.name,
                session_id=self.session.session_id,
                status=AgentStatus.FAILED,
                verdict="REJECT",
                confidence=0.0,
                details={"error": str(e)},
                error=str(e)
            )
    
    def parse_response(self, response: GeminiResponse) -> AgentResult:
        """Parse Gemini response into authorization validation result."""
        try:
            # Extract JSON from response
            content = response.content.strip()
            
            # Try to find JSON in the response
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    raise ValueError("No JSON found in response")
            
            # Parse JSON
            analysis_data = json.loads(json_str)
            
            # Extract key information
            authorization_report = analysis_data.get("authorization_report", {})
            checks = analysis_data.get("checks", [])
            authorization_summary = analysis_data.get("authorization_summary", {})
            
            # Determine verdict based on authorization status
            overall_status = authorization_summary.get("overall_status", "unauthorized")
            critical_issues = authorization_summary.get("critical_issues", 0)
            security_violations = authorization_summary.get("security_violations", 0)
            
            if critical_issues > 0 or security_violations > 0:
                verdict = "ISOLATE"
            elif overall_status == "unauthorized":
                verdict = "REJECT"
            elif overall_status == "partial":
                verdict = "REJECT"
            else:
                verdict = "APPROVE"
            
            # Calculate confidence
            confidence = self._calculate_confidence(analysis_data)
            
            # Prepare details
            details = {
                "authorization_report": authorization_report,
                "checks": checks,
                "recommendations": analysis_data.get("recommendations", []),
                "authorization_summary": authorization_summary,
                "total_checks": len(checks),
                "authorized_checks": sum(1 for c in checks if c.get("status") == "authorized"),
                "unauthorized_checks": sum(1 for c in checks if c.get("status") == "unauthorized")
            }
            
            return AgentResult(
                agent_name=self.name,
                session_id=self.session.session_id,
                status=AgentStatus.COMPLETED,
                verdict=verdict,
                confidence=confidence,
                details=details
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse authorization response: {e}")
            return AgentResult(
                agent_name=self.name,
                session_id=self.session.session_id,
                status=AgentStatus.FAILED,
                verdict="REJECT",
                confidence=0.0,
                details={"error": f"Parse error: {str(e)}"},
                error=str(e)
            )
    
    def _prepare_analysis_context(self, deployment_context: Dict[str, Any]) -> Dict[str, str]:
        """Prepare context for authorization analysis."""
        return {
            "commit_hash": deployment_context.get("commit_hash", "unknown"),
            "author_metadata": json.dumps(deployment_context.get("author_metadata", {}), indent=2),
            "access_controls": json.dumps(deployment_context.get("access_controls", {}), indent=2),
            "deployment_context": json.dumps(deployment_context, indent=2),
            "security_requirements": json.dumps(self.security_requirements, indent=2)
        }
    
    def _perform_additional_authorization_checks(self, deployment_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform additional automated authorization checks."""
        checks = []
        
        # Check commit hash format
        commit_hash = deployment_context.get("commit_hash", "")
        if commit_hash and not self._is_valid_commit_hash(commit_hash):
            checks.append({
                "check_type": "commit_validation",
                "status": "unauthorized",
                "description": "Invalid commit hash format",
                "severity": "HIGH"
            })
        
        # Check author email format
        author_metadata = deployment_context.get("author_metadata", {})
        author_email = author_metadata.get("email", "")
        if author_email and not self._is_valid_email(author_email):
            checks.append({
                "check_type": "author_validation",
                "status": "unauthorized",
                "description": "Invalid author email format",
                "severity": "MEDIUM"
            })
        
        # Check for commit signing
        if not deployment_context.get("commit_signed", False):
            checks.append({
                "check_type": "commit_signing",
                "status": "unauthorized",
                "description": "Commit not signed",
                "severity": "HIGH"
            })
        
        return checks
    
    def _is_valid_commit_hash(self, commit_hash: str) -> bool:
        """Validate commit hash format."""
        import re
        return bool(re.match(r'^[a-f0-9]{40}$', commit_hash))
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        import re
        return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))
    
    def _calculate_confidence(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the authorization analysis."""
        base_confidence = 0.8
        
        # Increase confidence based on check diversity
        checks = analysis_data.get("checks", [])
        if checks:
            check_types = set(c.get("check_type", "") for c in checks)
            if len(check_types) > 3:
                base_confidence += 0.1
        
        # Increase confidence for detailed evidence
        evidence_count = sum(len(c.get("evidence", [])) for c in checks)
        if evidence_count > 10:
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _determine_threat_level(self, result: AgentResult) -> ThreatLevel:
        """Determine threat level based on authorization findings."""
        critical_issues = result.details.get("authorization_summary", {}).get("critical_issues", 0)
        security_violations = result.details.get("authorization_summary", {}).get("security_violations", 0)
        unauthorized_checks = result.details.get("unauthorized_checks", 0)
        
        if critical_issues > 0 or security_violations > 0:
            return ThreatLevel.CRITICAL
        elif unauthorized_checks > 3:
            return ThreatLevel.HIGH
        elif unauthorized_checks > 1:
            return ThreatLevel.MEDIUM
        elif unauthorized_checks > 0:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.INFO
    
    def _calculate_reward(self, result: AgentResult) -> float:
        """Calculate RL reward for authorization agent performance."""
        base_reward = super()._calculate_reward(result)
        
        # Additional reward for comprehensive authorization coverage
        total_checks = result.details.get("total_checks", 0)
        if total_checks > 5:
            base_reward += 0.2
        
        # Reward for identifying security violations
        security_violations = result.details.get("authorization_summary", {}).get("security_violations", 0)
        if security_violations > 0:
            base_reward += 0.3
        
        # Penalty for false positives (high unauthorized checks with low confidence)
        unauthorized_checks = result.details.get("unauthorized_checks", 0)
        if unauthorized_checks > 5 and result.confidence < 0.5:
            base_reward -= 0.2
        
        return max(-1.0, min(1.0, base_reward))
