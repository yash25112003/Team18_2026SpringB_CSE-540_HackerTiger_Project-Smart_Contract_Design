"""
Compliance Agent (Regulo-Guardian) - Regulatory/policy compliance validation.
Checks for GDPR, SOC2, data/privacy, logging, and dynamically updated compliance policies.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from agents.base_agent import ValidatorAgent, AgentResult, AgentStatus
from utils.gemini_api import GeminiResponse
from system_constitution import ThreatLevel, CONSTITUTION


class ComplianceFramework(Enum):
    """Compliance frameworks to check against."""
    GDPR = "gdpr"
    SOC2 = "soc2"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"
    NIST = "nist"
    CCPA = "ccpa"


@dataclass
class ComplianceFinding:
    """Structured compliance finding."""
    framework: ComplianceFramework
    requirement: str
    status: str  # "COMPLIANT", "NON_COMPLIANT", "PARTIAL"
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    description: str
    evidence: List[str]
    remediation: str
    references: List[str]


@dataclass
class ComplianceReport:
    """Comprehensive compliance validation report."""
    frameworks_checked: List[ComplianceFramework]
    total_requirements: int
    compliant_requirements: int
    non_compliant_requirements: int
    partial_requirements: int
    compliance_score: float
    findings: List[ComplianceFinding]
    recommendations: List[str]


class ComplianceAgent(ValidatorAgent):
    """
    Regulo-Guardian: Compliance validation agent for regulatory and policy compliance.
    Checks GDPR, SOC2, data/privacy, logging, and dynamically updated compliance policies.
    """
    
    def __init__(self, gemini_api, audit_logger, session, config=None):
        super().__init__("Regulo-Guardian", gemini_api, audit_logger, session, config)
        
        # Compliance requirements mapping
        self.compliance_requirements = {
            ComplianceFramework.GDPR: {
                "data_protection": ["Data minimization", "Purpose limitation", "Storage limitation"],
                "privacy_rights": ["Right to access", "Right to rectification", "Right to erasure"],
                "consent": ["Explicit consent", "Withdrawal of consent", "Consent records"],
                "security": ["Data encryption", "Access controls", "Breach notification"]
            },
            ComplianceFramework.SOC2: {
                "security": ["Access controls", "System monitoring", "Data encryption"],
                "availability": ["System uptime", "Backup procedures", "Disaster recovery"],
                "processing_integrity": ["Data accuracy", "Processing controls", "Error handling"],
                "confidentiality": ["Data classification", "Access restrictions", "Data handling"],
                "privacy": ["Data collection", "Data use", "Data retention"]
            },
            ComplianceFramework.HIPAA: {
                "administrative_safeguards": ["Security officer", "Workforce training", "Access management"],
                "physical_safeguards": ["Facility access", "Workstation use", "Device controls"],
                "technical_safeguards": ["Access control", "Audit controls", "Integrity", "Transmission security"]
            }
        }
        
        # Data classification levels
        self.data_classification = {
            "public": {"encryption": False, "access_controls": "Basic"},
            "internal": {"encryption": True, "access_controls": "Role-based"},
            "confidential": {"encryption": True, "access_controls": "Strict"},
            "restricted": {"encryption": True, "access_controls": "Maximum"}
        }
    
    def get_prompt_template(self) -> str:
        """Get the compliance validation prompt template."""
        return """
You are Regulo-Guardian, a compliance validation agent specializing in regulatory and policy compliance. Your mission is to check deployments for GDPR, SOC2, data/privacy, logging, and dynamically updated compliance policies.

## Analysis Context:
- Deployment Context: {deployment_context}
- Data Types: {data_types}
- Privacy Requirements: {privacy_requirements}
- Security Controls: {security_controls}
- Logging Configuration: {logging_config}

## Your Compliance Framework:

### 1. GDPR Compliance
- **Data Protection**: Data minimization, purpose limitation, storage limitation
- **Privacy Rights**: Right to access, rectification, erasure, portability
- **Consent Management**: Explicit consent, withdrawal mechanisms, consent records
- **Security Measures**: Data encryption, access controls, breach notification
- **Data Processing**: Lawful basis, data subject rights, cross-border transfers

### 2. SOC2 Compliance
- **Security**: Access controls, system monitoring, data encryption
- **Availability**: System uptime, backup procedures, disaster recovery
- **Processing Integrity**: Data accuracy, processing controls, error handling
- **Confidentiality**: Data classification, access restrictions, data handling
- **Privacy**: Data collection, use, retention, and disposal

### 3. Data Privacy
- **Data Classification**: Public, internal, confidential, restricted
- **Data Handling**: Collection, processing, storage, transmission, disposal
- **Privacy Controls**: Anonymization, pseudonymization, consent management
- **Data Subject Rights**: Access, rectification, erasure, portability, objection

### 4. Logging and Monitoring
- **Audit Logging**: Comprehensive logging of all activities
- **Log Retention**: Appropriate retention periods
- **Log Security**: Log integrity, access controls, tamper protection
- **Monitoring**: Real-time monitoring, alerting, incident response

### 5. Dynamic Policy Updates
- **Policy Versioning**: Track policy changes and updates
- **Compliance Mapping**: Map requirements to implementations
- **Gap Analysis**: Identify compliance gaps and remediation
- **Continuous Monitoring**: Ongoing compliance validation

## Output Format:
Provide a comprehensive compliance analysis in the following JSON structure:

```json
{{
    "compliance_report": {{
        "frameworks_checked": ["gdpr", "soc2", "hipaa"],
        "total_requirements": integer,
        "compliant_requirements": integer,
        "non_compliant_requirements": integer,
        "partial_requirements": integer,
        "compliance_score": float (0.0-1.0)
    }},
    "findings": [
        {{
            "framework": "gdpr|soc2|hipaa|pci_dss|iso27001",
            "requirement": "Specific compliance requirement",
            "status": "COMPLIANT|NON_COMPLIANT|PARTIAL",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "description": "Detailed compliance assessment",
            "evidence": ["evidence1", "evidence2"],
            "remediation": "Specific remediation steps",
            "references": ["reference1", "reference2"]
        }}
    ],
    "recommendations": [
        "Priority compliance recommendations"
    ],
    "compliance_summary": {{
        "overall_status": "COMPLIANT|NON_COMPLIANT|PARTIAL",
        "critical_issues": integer,
        "high_priority_issues": integer,
        "compliance_gaps": ["gap1", "gap2"],
        "next_steps": ["step1", "step2"]
    }}
}}
```

## Compliance Guidelines:
1. **Be thorough** - Check all applicable compliance requirements
2. **Be specific** - Provide detailed evidence and remediation
3. **Prioritize impact** - Focus on critical compliance violations
4. **Consider context** - Compliance varies by jurisdiction and industry
5. **Provide evidence** - Support findings with specific data points
6. **Suggest improvements** - Always recommend compliance enhancements

Analyze the provided deployment context for regulatory and policy compliance.
"""
    
    async def validate(self, deployment_context: Dict[str, Any]) -> AgentResult:
        """
        Perform comprehensive compliance validation.
        
        Args:
            deployment_context: Deployment context to analyze
            
        Returns:
            AgentResult: Compliance validation result
        """
        try:
            # Prepare analysis context
            analysis_context = self._prepare_analysis_context(deployment_context)
            
            # Generate compliance validation prompt
            prompt = self.get_prompt_template().format(**analysis_context)
            
            # Call Gemini for analysis
            response = await self._call_gemini(prompt)
            
            # Parse and validate response
            result = self.parse_response(response)
            
            # Perform additional compliance checks
            additional_checks = self._perform_additional_compliance_checks(deployment_context)
            
            # Merge results
            if additional_checks:
                result.details["additional_compliance_checks"] = additional_checks
            
            # Determine threat level
            result.threat_level = self._determine_threat_level(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Compliance validation failed: {e}")
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
        """Parse Gemini response into compliance validation result."""
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
            compliance_report = analysis_data.get("compliance_report", {})
            findings = analysis_data.get("findings", [])
            compliance_summary = analysis_data.get("compliance_summary", {})
            
            # Determine verdict based on compliance status
            overall_status = compliance_summary.get("overall_status", "NON_COMPLIANT")
            critical_issues = compliance_summary.get("critical_issues", 0)
            
            if critical_issues > 0:
                verdict = "ISOLATE"
            elif overall_status == "NON_COMPLIANT":
                verdict = "REJECT"
            elif overall_status == "PARTIAL":
                verdict = "REJECT"
            else:
                verdict = "APPROVE"
            
            # Calculate confidence
            confidence = self._calculate_confidence(analysis_data)
            
            # Prepare details
            details = {
                "compliance_report": compliance_report,
                "findings": findings,
                "recommendations": analysis_data.get("recommendations", []),
                "compliance_summary": compliance_summary,
                "total_findings": len(findings),
                "critical_findings": sum(1 for f in findings if f.get("severity") == "CRITICAL"),
                "non_compliant_findings": sum(1 for f in findings if f.get("status") == "NON_COMPLIANT")
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
            self.logger.error(f"Failed to parse compliance response: {e}")
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
        """Prepare context for compliance analysis."""
        return {
            "deployment_context": json.dumps(deployment_context, indent=2),
            "data_types": json.dumps(deployment_context.get("data_types", []), indent=2),
            "privacy_requirements": json.dumps(deployment_context.get("privacy_requirements", {}), indent=2),
            "security_controls": json.dumps(deployment_context.get("security_controls", {}), indent=2),
            "logging_config": json.dumps(deployment_context.get("logging_config", {}), indent=2)
        }
    
    def _perform_additional_compliance_checks(self, deployment_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform additional automated compliance checks."""
        checks = []
        
        # Check data classification
        data_types = deployment_context.get("data_types", [])
        for data_type in data_types:
            if "personal" in data_type.lower() or "pii" in data_type.lower():
                checks.append({
                    "check": "data_classification",
                    "status": "COMPLIANT" if "encryption" in str(deployment_context) else "NON_COMPLIANT",
                    "description": "Personal data encryption check",
                    "severity": "HIGH"
                })
        
        # Check logging configuration
        logging_config = deployment_context.get("logging_config", {})
        if not logging_config.get("audit_logging", False):
            checks.append({
                "check": "audit_logging",
                "status": "NON_COMPLIANT",
                "description": "Audit logging not enabled",
                "severity": "MEDIUM"
            })
        
        return checks
    
    def _calculate_confidence(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the compliance analysis."""
        base_confidence = 0.8
        
        # Increase confidence based on framework coverage
        compliance_report = analysis_data.get("compliance_report", {})
        frameworks_checked = compliance_report.get("frameworks_checked", [])
        if len(frameworks_checked) > 2:
            base_confidence += 0.1
        
        # Increase confidence for detailed findings
        findings = analysis_data.get("findings", [])
        if len(findings) > 5:
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _determine_threat_level(self, result: AgentResult) -> ThreatLevel:
        """Determine threat level based on compliance findings."""
        critical_findings = result.details.get("critical_findings", 0)
        non_compliant_findings = result.details.get("non_compliant_findings", 0)
        
        if critical_findings > 0:
            return ThreatLevel.CRITICAL
        elif non_compliant_findings > 3:
            return ThreatLevel.HIGH
        elif non_compliant_findings > 1:
            return ThreatLevel.MEDIUM
        elif non_compliant_findings > 0:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.INFO
    
    def _calculate_reward(self, result: AgentResult) -> float:
        """Calculate RL reward for compliance agent performance."""
        base_reward = super()._calculate_reward(result)
        
        # Additional reward for comprehensive compliance coverage
        total_findings = result.details.get("total_findings", 0)
        if total_findings > 10:
            base_reward += 0.2
        
        # Reward for identifying critical compliance issues
        critical_findings = result.details.get("critical_findings", 0)
        if critical_findings > 0:
            base_reward += 0.3
        
        # Penalty for false positives (high findings with low confidence)
        if total_findings > 20 and result.confidence < 0.5:
            base_reward -= 0.2
        
        return max(-1.0, min(1.0, base_reward))
