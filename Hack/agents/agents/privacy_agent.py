"""
Privacy Agent (Data-Sentry) - Detect PII leaks and data exposures.
Scans for personally identifiable information and sensitive data leaks.
"""

import json
import re
import asyncio
from typing import Dict, Any, List, Optional
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


class DataType(Enum):
    """Types of sensitive data to detect."""
    PII = "pii"
    PHI = "phi"
    FINANCIAL = "financial"
    CREDENTIALS = "credentials"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    TRADE_SECRETS = "trade_secrets"


class PrivacyViolation(Enum):
    """Types of privacy violations."""
    DATA_EXPOSURE = "data_exposure"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_BREACH = "data_breach"
    PRIVACY_LEAK = "privacy_leak"
    CONSENT_VIOLATION = "consent_violation"


@dataclass
class PrivacyFinding:
    """Structured privacy finding."""
    data_type: DataType
    violation_type: PrivacyViolation
    severity: str
    description: str
    evidence: List[str]
    risk_factors: List[str]
    recommendations: List[str]


class PrivacyAgent(ValidatorAgent):
    """
    Data-Sentry: Privacy watchdog agent for PII and sensitive data detection.
    Scans for leaks, exposures, and privacy violations.
    """
    
    def __init__(self, gemini_api, audit_logger, session, config=None):
        super().__init__("Data-Sentry", gemini_api, audit_logger, session, config)
        
        # PII patterns
        self.pii_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            "address": r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Way|Boulevard|Blvd)\b'
        }
        
        # Sensitive data patterns
        self.sensitive_patterns = {
            "api_key": r'api[_-]?key["\']?\s*[:=]\s*["\']?[A-Za-z0-9]{20,}["\']?',
            "password": r'password["\']?\s*[:=]\s*["\']?[^"\'\s]+["\']?',
            "token": r'token["\']?\s*[:=]\s*["\']?[A-Za-z0-9]{20,}["\']?',
            "secret": r'secret["\']?\s*[:=]\s*["\']?[A-Za-z0-9]{10,}["\']?'
        }
    
    def get_prompt_template(self) -> str:
        """Get the privacy validation prompt template."""
        return """
You are Data-Sentry, a privacy watchdog agent specializing in PII and sensitive data detection. Your mission is to scan for leaks, exposures, and privacy violations in deployments.

## Analysis Context:
- Deployment Context: {deployment_context}
- Data Content: {data_content}
- Privacy Requirements: {privacy_requirements}
- Data Classification: {data_classification}

## Your Privacy Framework:

### 1. PII Detection
- **Personal Information**: Names, addresses, phone numbers, emails
- **Identity Information**: SSNs, driver's licenses, passport numbers
- **Contact Information**: Phone numbers, email addresses, physical addresses
- **Demographic Information**: Age, gender, race, ethnicity

### 2. Sensitive Data Detection
- **Financial Data**: Credit card numbers, bank accounts, financial records
- **Health Information**: Medical records, health conditions, treatments
- **Credentials**: Passwords, API keys, tokens, secrets
- **Intellectual Property**: Trade secrets, proprietary information, patents

### 3. Privacy Violation Analysis
- **Data Exposure**: Unauthorized data exposure or leakage
- **Unauthorized Access**: Access without proper authorization
- **Data Breach**: Confirmed or suspected data breaches
- **Consent Violation**: Processing without proper consent

### 4. Risk Assessment
- **Data Sensitivity**: Assess sensitivity level of detected data
- **Exposure Risk**: Evaluate risk of data exposure
- **Compliance Risk**: Assess compliance with privacy regulations
- **Business Impact**: Evaluate potential business impact

## Output Format:
Provide a comprehensive privacy analysis in the following JSON structure:

```json
{{
    "privacy_issues": [
        {{
            "data_type": "pii|phi|financial|credentials|intellectual_property|trade_secrets",
            "violation_type": "data_exposure|unauthorized_access|data_breach|privacy_leak|consent_violation",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "description": "Detailed description of the privacy issue",
            "evidence": ["evidence1", "evidence2"],
            "risk_factors": ["factor1", "factor2"],
            "recommendations": ["recommendation1", "recommendation2"]
        }}
    ],
    "severity": integer (1-10),
    "privacy_summary": {{
        "total_issues": integer,
        "critical_issues": integer,
        "high_risk_issues": integer,
        "data_types_found": ["type1", "type2"],
        "compliance_status": "COMPLIANT|NON_COMPLIANT|PARTIAL"
    }},
    "recommendations": [
        "Priority privacy protection recommendations"
    ]
}}
```

## Privacy Guidelines:
1. **Be thorough** - Scan all data for privacy issues
2. **Be specific** - Provide detailed evidence and descriptions
3. **Be protective** - Err on the side of caution for privacy
4. **Be compliant** - Consider privacy regulations and requirements
5. **Be actionable** - Provide specific remediation steps
6. **Be comprehensive** - Cover all aspects of data privacy

Analyze the provided deployment context for privacy issues and data protection.
"""
    
    async def validate(self, deployment_context: Dict[str, Any]) -> AgentResult:
        """
        Perform comprehensive privacy validation.
        
        Args:
            deployment_context: Deployment context to analyze
            
        Returns:
            AgentResult: Privacy validation result
        """
        try:
            # Prepare analysis context
            analysis_context = self._prepare_analysis_context(deployment_context)
            
            # Generate privacy validation prompt
            prompt = self.get_prompt_template().format(**analysis_context)
            
            # Call Gemini for analysis
            response = await self._call_gemini(prompt)
            
            # Parse and validate response
            result = self.parse_response(response)
            
            # Perform additional pattern matching
            pattern_findings = self._perform_pattern_matching(deployment_context)
            
            # Merge results
            if pattern_findings:
                result.details["pattern_findings"] = pattern_findings
                result.details["total_issues"] = (
                    result.details.get("total_issues", 0) + len(pattern_findings)
                )
            
            # Determine threat level
            result.threat_level = self._determine_threat_level(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Privacy validation failed: {e}")
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
        """Parse Gemini response into privacy validation result."""
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
            privacy_issues = analysis_data.get("privacy_issues", [])
            severity = analysis_data.get("severity", 1)
            privacy_summary = analysis_data.get("privacy_summary", {})
            
            # Determine verdict based on privacy issues
            critical_issues = privacy_summary.get("critical_issues", 0)
            high_risk_issues = privacy_summary.get("high_risk_issues", 0)
            
            if critical_issues > 0:
                verdict = "ISOLATE"
            elif high_risk_issues > 0 or severity >= 7:
                verdict = "REJECT"
            elif severity >= 4:
                verdict = "REJECT"
            else:
                verdict = "APPROVE"
            
            # Calculate confidence
            confidence = self._calculate_confidence(analysis_data)
            
            # Prepare details
            details = {
                "privacy_issues": privacy_issues,
                "severity": severity,
                "privacy_summary": privacy_summary,
                "recommendations": analysis_data.get("recommendations", []),
                "total_issues": len(privacy_issues),
                "critical_issues": critical_issues,
                "high_risk_issues": high_risk_issues
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
            self.logger.error(f"Failed to parse privacy response: {e}")
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
        """Prepare context for privacy analysis."""
        return {
            "deployment_context": json.dumps(deployment_context, indent=2),
            "data_content": json.dumps(deployment_context.get("data_content", ""), indent=2),
            "privacy_requirements": json.dumps(deployment_context.get("privacy_requirements", {}), indent=2),
            "data_classification": json.dumps(deployment_context.get("data_classification", {}), indent=2)
        }
    
    def _perform_pattern_matching(self, deployment_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform pattern matching for PII and sensitive data."""
        findings = []
        
        # Get data content
        data_content = deployment_context.get("data_content", "")
        if not data_content:
            return findings
        
        # Check for PII patterns
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, data_content, re.IGNORECASE)
            if matches:
                findings.append({
                    "data_type": "pii",
                    "violation_type": "data_exposure",
                    "severity": "HIGH",
                    "description": f"Potential {pii_type} detected: {len(matches)} matches",
                    "evidence": matches[:5],  # Limit to 5 matches
                    "risk_factors": ["PII exposure", "Privacy violation"],
                    "recommendations": [f"Remove or mask {pii_type}", "Implement data anonymization"]
                })
        
        # Check for sensitive data patterns
        for sensitive_type, pattern in self.sensitive_patterns.items():
            matches = re.findall(pattern, data_content, re.IGNORECASE)
            if matches:
                findings.append({
                    "data_type": "credentials",
                    "violation_type": "data_exposure",
                    "severity": "CRITICAL",
                    "description": f"Potential {sensitive_type} detected: {len(matches)} matches",
                    "evidence": matches[:3],  # Limit to 3 matches
                    "risk_factors": ["Credential exposure", "Security violation"],
                    "recommendations": [f"Remove {sensitive_type} from code", "Use environment variables"]
                })
        
        return findings
    
    def _calculate_confidence(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the privacy analysis."""
        base_confidence = 0.8
        
        # Increase confidence based on issue diversity
        privacy_issues = analysis_data.get("privacy_issues", [])
        if privacy_issues:
            data_types = set(issue.get("data_type", "") for issue in privacy_issues)
            if len(data_types) > 2:
                base_confidence += 0.1
        
        # Increase confidence for detailed evidence
        evidence_count = sum(len(issue.get("evidence", [])) for issue in privacy_issues)
        if evidence_count > 5:
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _determine_threat_level(self, result: AgentResult) -> ThreatLevel:
        """Determine threat level based on privacy findings."""
        critical_issues = result.details.get("critical_issues", 0)
        high_risk_issues = result.details.get("high_risk_issues", 0)
        severity = result.details.get("severity", 1)
        
        if critical_issues > 0 or severity >= 8:
            return ThreatLevel.CRITICAL
        elif high_risk_issues > 0 or severity >= 6:
            return ThreatLevel.HIGH
        elif severity >= 4:
            return ThreatLevel.MEDIUM
        elif severity >= 2:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.INFO
    
    def _calculate_reward(self, result: AgentResult) -> float:
        """Calculate RL reward for privacy agent performance."""
        base_reward = super()._calculate_reward(result)
        
        # Additional reward for privacy issue detection
        total_issues = result.details.get("total_issues", 0)
        if total_issues > 0:
            base_reward += 0.2
        
        # Reward for critical issue detection
        critical_issues = result.details.get("critical_issues", 0)
        if critical_issues > 0:
            base_reward += 0.3
        
        # Penalty for false positives (high issues with low confidence)
        if total_issues > 10 and result.confidence < 0.5:
            base_reward -= 0.2
        
        return max(-1.0, min(1.0, base_reward))
