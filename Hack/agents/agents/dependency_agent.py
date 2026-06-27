"""
Dependency Agent (DepAware) - Analyzes upstream/deprecated supply chain risks.
Audits all dependencies for deprecation, vulnerabilities, and risky upstream updates.
"""

import json
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


class DependencyRisk(Enum):
    """Types of dependency risks."""
    VULNERABILITY = "vulnerability"
    DEPRECATION = "deprecation"
    MAINTENANCE = "maintenance"
    LICENSE = "license"
    SUPPLY_CHAIN = "supply_chain"


@dataclass
class DependencyFinding:
    """Structured dependency finding."""
    package_name: str
    current_version: str
    latest_version: str
    risk_type: DependencyRisk
    severity: str
    description: str
    cve_ids: List[str]
    recommendations: List[str]


class DependencyAgent(ValidatorAgent):
    """
    DepAware: Dependency intelligence agent for supply chain risk analysis.
    Audits dependencies for vulnerabilities, deprecation, and maintenance risks.
    """
    
    def __init__(self, gemini_api, audit_logger, session, config=None):
        super().__init__("DepAware", gemini_api, audit_logger, session, config)
        
        # Known vulnerable packages (simplified)
        self.vulnerable_packages = {
            "log4j": ["CVE-2021-44228", "CVE-2021-45046"],
            "spring": ["CVE-2022-22965", "CVE-2022-22963"],
            "openssl": ["CVE-2014-0160"],
            "jquery": ["CVE-2020-11022", "CVE-2020-11023"]
        }
        
        # Deprecated packages
        self.deprecated_packages = {
            "python2": "Python 2 is end-of-life",
            "node6": "Node.js 6 is end-of-life",
            "react15": "React 15 is deprecated"
        }
    
    def get_prompt_template(self) -> str:
        """Get the dependency analysis prompt template."""
        return """
You are DepAware, a dependency intelligence agent specializing in supply chain risk analysis. Your mission is to audit all dependencies for vulnerabilities, deprecation, and maintenance risks.

## Analysis Context:
- Dependencies: {dependencies}
- Package Manager: {package_manager}
- Security Requirements: {security_requirements}
- Deployment Context: {deployment_context}

## Your Dependency Framework:

### 1. Vulnerability Analysis
- **CVE Scanning**: Check for known vulnerabilities
- **Security Advisories**: Review security advisories
- **Exploit Availability**: Check for available exploits
- **Patch Status**: Verify patch availability

### 2. Maintenance Analysis
- **Active Maintenance**: Check if package is actively maintained
- **Update Frequency**: Analyze update patterns
- **Community Support**: Assess community support level
- **Documentation Quality**: Evaluate documentation

### 3. Deprecation Analysis
- **End-of-Life**: Check for end-of-life packages
- **Deprecation Warnings**: Look for deprecation notices
- **Replacement Packages**: Identify replacement options
- **Migration Paths**: Assess migration complexity

### 4. License Analysis
- **License Compatibility**: Check license compatibility
- **License Risks**: Identify license risks
- **Commercial Use**: Verify commercial use permissions
- **Attribution Requirements**: Check attribution needs

### 5. Supply Chain Analysis
- **Upstream Dependencies**: Analyze upstream dependencies
- **Transitive Dependencies**: Check transitive dependency risks
- **Package Integrity**: Verify package integrity
- **Distribution Channels**: Assess distribution security

## Output Format:
Provide a comprehensive dependency analysis in the following JSON structure:

```json
{{
    "risk_dependencies": [
        {{
            "package_name": "package_name",
            "current_version": "current_version",
            "latest_version": "latest_version",
            "risk_type": "vulnerability|deprecation|maintenance|license|supply_chain",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "description": "Detailed risk description",
            "cve_ids": ["CVE-XXXX-XXXX"],
            "recommendations": ["recommendation1", "recommendation2"]
        }}
    ],
    "alternatives": [
        {{
            "package_name": "alternative_package",
            "reason": "Why this is a better alternative",
            "migration_effort": "LOW|MEDIUM|HIGH"
        }}
    ],
    "dependency_summary": {{
        "total_dependencies": integer,
        "risky_dependencies": integer,
        "critical_risks": integer,
        "maintenance_issues": integer,
        "license_issues": integer
    }},
    "recommendations": [
        "Priority dependency management recommendations"
    ]
}}
```

## Dependency Guidelines:
1. **Be thorough** - Check all dependencies comprehensively
2. **Be current** - Use latest vulnerability databases
3. **Be practical** - Provide actionable recommendations
4. **Be risk-aware** - Prioritize high-risk dependencies
5. **Be forward-looking** - Consider long-term maintenance
6. **Be compliant** - Ensure license compliance

Analyze the provided dependencies for supply chain risks and vulnerabilities.
"""
    
    async def validate(self, deployment_context: Dict[str, Any]) -> AgentResult:
        """
        Perform comprehensive dependency validation.
        
        Args:
            deployment_context: Deployment context to analyze
            
        Returns:
            AgentResult: Dependency validation result
        """
        try:
            # Prepare analysis context
            analysis_context = self._prepare_analysis_context(deployment_context)
            
            # Generate dependency validation prompt
            prompt = self.get_prompt_template().format(**analysis_context)
            
            # Call Gemini for analysis
            response = await self._call_gemini(prompt)
            
            # Parse and validate response
            result = self.parse_response(response)
            
            # Perform additional dependency checks
            additional_checks = self._perform_additional_dependency_checks(deployment_context)
            
            # Merge results
            if additional_checks:
                result.details["additional_checks"] = additional_checks
            
            # Determine threat level
            result.threat_level = self._determine_threat_level(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Dependency validation failed: {e}")
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
        """Parse Gemini response into dependency validation result."""
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
            risk_dependencies = analysis_data.get("risk_dependencies", [])
            alternatives = analysis_data.get("alternatives", [])
            dependency_summary = analysis_data.get("dependency_summary", {})
            
            # Determine verdict based on dependency risks
            critical_risks = dependency_summary.get("critical_risks", 0)
            risky_dependencies = dependency_summary.get("risky_dependencies", 0)
            
            if critical_risks > 0:
                verdict = "ISOLATE"
            elif risky_dependencies > 3:
                verdict = "REJECT"
            elif risky_dependencies > 0:
                verdict = "REJECT"
            else:
                verdict = "APPROVE"
            
            # Calculate confidence
            confidence = self._calculate_confidence(analysis_data)
            
            # Prepare details
            details = {
                "risk_dependencies": risk_dependencies,
                "alternatives": alternatives,
                "dependency_summary": dependency_summary,
                "recommendations": analysis_data.get("recommendations", []),
                "total_dependencies": dependency_summary.get("total_dependencies", 0),
                "risky_dependencies": risky_dependencies,
                "critical_risks": critical_risks
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
            self.logger.error(f"Failed to parse dependency response: {e}")
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
        """Prepare context for dependency analysis."""
        return {
            "dependencies": json.dumps(deployment_context.get("dependencies", {}), indent=2),
            "package_manager": deployment_context.get("package_manager", "unknown"),
            "security_requirements": json.dumps(deployment_context.get("security_requirements", {}), indent=2),
            "deployment_context": json.dumps(deployment_context, indent=2)
        }
    
    def _perform_additional_dependency_checks(self, deployment_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform additional automated dependency checks."""
        checks = []
        
        # Check dependencies against known vulnerable packages
        dependencies = deployment_context.get("dependencies", {})
        for package_name, version in dependencies.items():
            if package_name.lower() in self.vulnerable_packages:
                cves = self.vulnerable_packages[package_name.lower()]
                checks.append({
                    "package_name": package_name,
                    "current_version": version,
                    "risk_type": "vulnerability",
                    "severity": "CRITICAL",
                    "description": f"Known vulnerabilities in {package_name}",
                    "cve_ids": cves,
                    "recommendations": [f"Update {package_name} to latest version", "Review CVE details"]
                })
            
            # Check for deprecated packages
            if package_name.lower() in self.deprecated_packages:
                reason = self.deprecated_packages[package_name.lower()]
                checks.append({
                    "package_name": package_name,
                    "current_version": version,
                    "risk_type": "deprecation",
                    "severity": "HIGH",
                    "description": f"Deprecated package: {reason}",
                    "cve_ids": [],
                    "recommendations": [f"Replace {package_name} with modern alternative", "Plan migration strategy"]
                })
        
        return checks
    
    def _calculate_confidence(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the dependency analysis."""
        base_confidence = 0.8
        
        # Increase confidence based on dependency coverage
        dependency_summary = analysis_data.get("dependency_summary", {})
        total_dependencies = dependency_summary.get("total_dependencies", 0)
        if total_dependencies > 10:
            base_confidence += 0.1
        
        # Increase confidence for detailed alternatives
        alternatives = analysis_data.get("alternatives", [])
        if alternatives:
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _determine_threat_level(self, result: AgentResult) -> ThreatLevel:
        """Determine threat level based on dependency findings."""
        critical_risks = result.details.get("critical_risks", 0)
        risky_dependencies = result.details.get("risky_dependencies", 0)
        
        if critical_risks > 0:
            return ThreatLevel.CRITICAL
        elif risky_dependencies > 3:
            return ThreatLevel.HIGH
        elif risky_dependencies > 1:
            return ThreatLevel.MEDIUM
        elif risky_dependencies > 0:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.INFO
    
    def _calculate_reward(self, result: AgentResult) -> float:
        """Calculate RL reward for dependency agent performance."""
        base_reward = super()._calculate_reward(result)
        
        # Additional reward for dependency risk detection
        risky_dependencies = result.details.get("risky_dependencies", 0)
        if risky_dependencies > 0:
            base_reward += 0.2
        
        # Reward for critical risk detection
        critical_risks = result.details.get("critical_risks", 0)
        if critical_risks > 0:
            base_reward += 0.3
        
        # Reward for providing alternatives
        alternatives = result.details.get("alternatives", [])
        if alternatives:
            base_reward += 0.1
        
        return max(-1.0, min(1.0, base_reward))
