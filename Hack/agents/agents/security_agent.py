"""
Security Agent (Securo-Sentinel) - Advanced cybersecurity validation with bug bar scoring.
Implements Microsoft Red Team methodologies and CVE analysis.
"""

import json
import re
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

try:
    from agents.base_agent import ValidatorAgent, AgentResult, AgentStatus
    from utils.gemini_api import GeminiResponse
    from system_constitution import ThreatLevel, CONSTITUTION
except ImportError:
    # For standalone execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agents.base_agent import ValidatorAgent, AgentResult, AgentStatus
    from utils.gemini_api import GeminiResponse
    from system_constitution import ThreatLevel, CONSTITUTION
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agents.base_agent import ValidatorAgent, AgentResult, AgentStatus
    from utils.gemini_api import GeminiResponse
    from system_constitution import ThreatLevel, CONSTITUTION


@dataclass
class VulnerabilityFinding:
    """Structured vulnerability finding."""
    cve_id: Optional[str]
    title: str
    description: str
    severity: str
    bug_bar_score: int
    exploitability: str
    impact: str
    remediation: str
    references: List[str]


@dataclass
class SecurityReport:
    """Comprehensive security analysis report."""
    total_findings: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    info_findings: int
    bug_bar_score: int
    vulnerabilities: List[VulnerabilityFinding]
    recommendations: List[str]
    risk_score: float


class SecurityAgent(ValidatorAgent):
    """
    Securo-Sentinel: Advanced cybersecurity agent using Microsoft Red Team methodologies.
    Performs static/dynamic analysis, CVE scanning, and bug bar scoring.
    """
    
    def __init__(self, gemini_api, audit_logger, session, config=None):
        super().__init__("Securo-Sentinel", gemini_api, audit_logger, session, config)
        
        # Security-specific configuration
        self.bug_bar_thresholds = {
            "CRITICAL": 5,
            "HIGH": 4,
            "MEDIUM": 3,
            "LOW": 2,
            "INFO": 1
        }
        
        # Known vulnerability patterns
        self.vulnerability_patterns = {
            "sql_injection": r"(?i)(union\s+select|drop\s+table|insert\s+into|delete\s+from)",
            "xss": r"(?i)(<script|javascript:|onload=|onerror=)",
            "path_traversal": r"(?i)(\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c)",
            "command_injection": r"(?i)(system\(|exec\(|shell_exec\(|passthru\()",
            "ldap_injection": r"(?i)(\*\)|\(&|\(|\)|\\|/)",
            "xxe": r"(?i)(<!DOCTYPE|<ENTITY|<!ENTITY)",
            "ssrf": r"(?i)(http://|https://|ftp://|file://|gopher://)",
            "deserialization": r"(?i)(ObjectInputStream|pickle\.loads|unserialize\()",
            "crypto_weak": r"(?i)(md5|sha1|des|rc4|weak.*key)",
            "secrets": r"(?i)(password|secret|key|token|api_key|private_key)\s*[:=]\s*['\"][^'\"]+['\"]"
        }
        
        # CVE database patterns (simplified)
        self.cve_patterns = {
            "log4j": ["CVE-2021-44228", "CVE-2021-45046", "CVE-2021-45105"],
            "spring4shell": ["CVE-2022-22965", "CVE-2022-22963"],
            "heartbleed": ["CVE-2014-0160"],
            "shellshock": ["CVE-2014-6271", "CVE-2014-7169"]
        }
    
    def get_prompt_template(self) -> str:
        """Get the security analysis prompt template."""
        return """
You are Securo-Sentinel, an advanced cybersecurity agent specializing in vulnerability assessment and threat analysis. Your mission is to analyze code, configurations, and dependencies for security vulnerabilities using Microsoft Red Team methodologies and bug bar scoring.

## Analysis Context:
- Deployment Context: {deployment_context}
- Code/Configuration: {code_content}
- Dependencies: {dependencies}
- Infrastructure: {infrastructure}

## Your Analysis Framework:

### 1. Vulnerability Scanning
- Static code analysis for injection vulnerabilities (SQL, XSS, LDAP, Command)
- Configuration security assessment
- Dependency vulnerability scanning
- Secret and credential exposure detection
- Cryptographic weakness identification

### 2. Bug Bar Scoring (Microsoft Methodology)
Score each finding using the Microsoft Bug Bar:
- **Critical (5)**: Remote code execution, privilege escalation, data breach
- **High (4)**: Significant security impact, authentication bypass
- **Medium (3)**: Moderate security impact, information disclosure
- **Low (2)**: Minor security impact, best practice violations
- **Info (1)**: Informational findings, recommendations

### 3. Threat Modeling
- Identify attack vectors and entry points
- Assess exploitability and impact
- Evaluate defense in depth coverage
- Consider attacker skill levels and motivations

### 4. Red Team Perspective
- Think like an attacker
- Identify novel attack paths
- Consider chained vulnerabilities
- Assess business impact

## Output Format:
Provide a comprehensive security analysis in the following JSON structure:

```json
{{
    "pass_status": boolean,
    "report": "Detailed markdown security report",
    "bug_bar_score": integer (1-5),
    "vulnerabilities": [
        {{
            "cve_id": "CVE-XXXX-XXXX or null",
            "title": "Vulnerability title",
            "description": "Detailed description",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
            "bug_bar_score": integer,
            "exploitability": "EASY|MODERATE|DIFFICULT",
            "impact": "Description of potential impact",
            "remediation": "Specific remediation steps",
            "references": ["URL1", "URL2"]
        }}
    ],
    "recommendations": [
        "Priority security recommendations"
    ],
    "risk_score": float (0.0-10.0),
    "threat_model": {{
        "attack_vectors": ["vector1", "vector2"],
        "entry_points": ["point1", "point2"],
        "defense_coverage": "assessment",
        "business_impact": "assessment"
    }}
}}
```

## Analysis Guidelines:
1. **Be thorough but practical** - Focus on real, exploitable vulnerabilities
2. **Prioritize by impact** - Critical and high-severity findings first
3. **Provide actionable remediation** - Specific, implementable fixes
4. **Consider context** - Assess risk based on deployment environment
5. **Think like an attacker** - Identify novel attack paths
6. **Follow Microsoft Bug Bar** - Use consistent scoring methodology

Analyze the provided deployment context and provide a comprehensive security assessment.
"""
    
    async def validate(self, deployment_context: Dict[str, Any]) -> AgentResult:
        """
        Perform comprehensive security validation.
        
        Args:
            deployment_context: Deployment context to analyze
            
        Returns:
            AgentResult: Security validation result
        """
        try:
            # Prepare analysis context
            analysis_context = self._prepare_analysis_context(deployment_context)
            
            # Generate security analysis prompt
            prompt = self.get_prompt_template().format(**analysis_context)
            
            # Call Gemini for analysis
            response = await self._call_gemini(prompt)
            
            # Parse and validate response
            result = self.parse_response(response)
            
            # Perform additional static analysis
            static_findings = self._perform_static_analysis(deployment_context)
            
            # Merge findings
            if static_findings:
                result.details["static_analysis"] = static_findings
                result.details["total_findings"] = (
                    result.details.get("total_findings", 0) + len(static_findings)
                )
            
            # Determine threat level
            result.threat_level = self._determine_threat_level(result)
            
            return result
            
        except asyncio.TimeoutError as e:
            self.logger.error(f"Security validation timed out: {e}")
            return AgentResult(
                agent_name=self.name,
                session_id=self.session.session_id,
                status=AgentStatus.TIMEOUT,
                verdict="REJECT",
                confidence=0.0,
                details={"error": "timeout"},
                error="timeout"
            )
        except Exception as e:
            self.logger.error(f"Security validation failed: {e}")
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
        """Parse Gemini response into security analysis result."""
        try:
            # Extract JSON from response
            content = response.content.strip()
            
            # Try to find JSON in the response
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
            pass_status = analysis_data.get("pass_status", False)
            bug_bar_score = analysis_data.get("bug_bar_score", 1)
            risk_score = analysis_data.get("risk_score", 0.0)
            vulnerabilities = analysis_data.get("vulnerabilities", [])
            
            # Determine verdict
            if bug_bar_score >= 4:  # High or Critical
                verdict = "ISOLATE"
            elif bug_bar_score >= 3:  # Medium
                verdict = "REJECT"
            elif pass_status:
                verdict = "APPROVE"
            else:
                verdict = "REJECT"
            
            # Calculate confidence based on findings
            confidence = self._calculate_confidence(analysis_data)
            
            # Prepare details
            details = {
                "security_report": analysis_data.get("report", ""),
                "vulnerabilities": vulnerabilities,
                "recommendations": analysis_data.get("recommendations", []),
                "bug_bar_score": bug_bar_score,
                "risk_score": risk_score,
                "threat_model": analysis_data.get("threat_model", {}),
                "total_findings": len(vulnerabilities)
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
            self.logger.error(f"Failed to parse security response: {e}")
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
        """Prepare context for security analysis."""
        return {
            "deployment_context": json.dumps(deployment_context, indent=2),
            "code_content": deployment_context.get("code", "No code provided"),
            "dependencies": json.dumps(deployment_context.get("dependencies", {}), indent=2),
            "infrastructure": json.dumps(deployment_context.get("infrastructure", {}), indent=2)
        }
    
    def _perform_static_analysis(self, deployment_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform static analysis for common vulnerabilities."""
        findings = []
        
        # Analyze code content
        code_content = deployment_context.get("code", "")
        if code_content:
            for vuln_type, pattern in self.vulnerability_patterns.items():
                matches = re.findall(pattern, code_content, re.MULTILINE)
                if matches:
                    findings.append({
                        "type": vuln_type,
                        "severity": self._get_pattern_severity(vuln_type),
                        "matches": matches[:5],  # Limit to 5 matches
                        "description": f"Potential {vuln_type} vulnerability detected"
                    })
        
        # Analyze dependencies for known CVEs
        dependencies = deployment_context.get("dependencies", {})
        for dep_name, dep_version in dependencies.items():
            cve_findings = self._check_dependency_cves(dep_name, dep_version)
            findings.extend(cve_findings)
        
        return findings
    
    def _get_pattern_severity(self, vuln_type: str) -> str:
        """Get severity for vulnerability pattern."""
        severity_map = {
            "sql_injection": "HIGH",
            "command_injection": "CRITICAL",
            "xss": "MEDIUM",
            "path_traversal": "HIGH",
            "ldap_injection": "HIGH",
            "xxe": "HIGH",
            "ssrf": "MEDIUM",
            "deserialization": "HIGH",
            "crypto_weak": "MEDIUM",
            "secrets": "HIGH"
        }
        return severity_map.get(vuln_type, "LOW")
    
    def _check_dependency_cves(self, dep_name: str, dep_version: str) -> List[Dict[str, Any]]:
        """Check dependencies for known CVEs."""
        findings = []
        
        # Check against known CVE patterns
        for cve_category, cves in self.cve_patterns.items():
            if cve_category.lower() in dep_name.lower():
                for cve in cves:
                    findings.append({
                        "type": "cve",
                        "cve_id": cve,
                        "severity": "CRITICAL",
                        "description": f"Known CVE {cve} in dependency {dep_name}",
                        "remediation": f"Update {dep_name} to a patched version"
                    })
        
        return findings
    
    def _calculate_confidence(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the analysis."""
        base_confidence = 0.7
        
        # Increase confidence based on findings quality
        vulnerabilities = analysis_data.get("vulnerabilities", [])
        if vulnerabilities:
            # More findings = higher confidence
            confidence_boost = min(0.2, len(vulnerabilities) * 0.05)
            base_confidence += confidence_boost
        
        # Increase confidence for detailed threat model
        threat_model = analysis_data.get("threat_model", {})
        if threat_model and threat_model.get("attack_vectors"):
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _determine_threat_level(self, result: AgentResult) -> ThreatLevel:
        """Determine threat level based on analysis results."""
        bug_bar_score = result.details.get("bug_bar_score", 1)
        
        if bug_bar_score >= 5:
            return ThreatLevel.CRITICAL
        elif bug_bar_score >= 4:
            return ThreatLevel.HIGH
        elif bug_bar_score >= 3:
            return ThreatLevel.MEDIUM
        elif bug_bar_score >= 2:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.INFO
    
    def _calculate_reward(self, result: AgentResult) -> float:
        """Calculate RL reward for security agent performance."""
        base_reward = super()._calculate_reward(result)
        
        # Additional reward for threat detection
        if result.threat_level and result.threat_level.value >= ThreatLevel.HIGH.value:
            base_reward += 0.3
        
        # Reward for comprehensive analysis
        total_findings = result.details.get("total_findings", 0)
        if total_findings > 0:
            base_reward += 0.1
        
        # Penalty for false positives (low confidence, high findings)
        if result.confidence < 0.5 and total_findings > 10:
            base_reward -= 0.2
        
        return max(-1.0, min(1.0, base_reward))


# Standalone execution for testing
if __name__ == "__main__":
    import sys
    import asyncio
    from utils.config import load_config
    from utils.gemini_api import GeminiAPI
    from utils.session import Session
    from utils.logging_utils import AuditLogger
    
    async def main():
        if len(sys.argv) != 2:
            print("Usage: python security_agent.py <deployment_json_file>")
            sys.exit(1)
        
        # Load deployment context
        with open(sys.argv[1], 'r') as f:
            deployment_context = json.load(f)
        
        # Initialize components
        config = load_config()
        gemini_api = GeminiAPI(
            api_keys=config.gemini_api_keys,
            model=config.gemini_model,
            temperature=config.gemini_temperature
        )
        
        # Create mock session
        session = Session(
            session_id="test-session",
            created_at=datetime.now(),
            deployment_context=deployment_context
        )
        
        audit_logger = AuditLogger("test_audit.log")
        
        # Create and run security agent
        agent = SecurityAgent(gemini_api, audit_logger, session)
        result = await agent.execute(deployment_context)
        
        # Print results
        print("Security Agent Results:")
        print(json.dumps(result.to_dict(), indent=2))
        
        # Verify JSON structure
        assert "agent_name" in result.to_dict()
        assert "verdict" in result.to_dict()
        assert "confidence" in result.to_dict()
        assert "details" in result.to_dict()
        
        print("✓ Security Agent test passed - JSON structure is correct")
    
    asyncio.run(main())