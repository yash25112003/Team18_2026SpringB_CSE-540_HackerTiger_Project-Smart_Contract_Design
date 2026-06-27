"""
Ethical Agent (Ethos-Guardian) - Checks for AI ethics, fairness, and rule-of-law compliance.
Reviews deployment for alignment with AI ethics, fairness principles, and international legal mandates.
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


class EthicalPrinciple(Enum):
    """AI ethical principles to evaluate."""
    FAIRNESS = "fairness"
    TRANSPARENCY = "transparency"
    ACCOUNTABILITY = "accountability"
    PRIVACY = "privacy"
    HUMAN_AUTONOMY = "human_autonomy"
    NON_MALEFICENCE = "non_maleficence"
    BENEFICENCE = "beneficence"
    JUSTICE = "justice"


class EthicalViolation(Enum):
    """Types of ethical violations."""
    BIAS = "bias"
    DISCRIMINATION = "discrimination"
    PRIVACY_VIOLATION = "privacy_violation"
    AUTONOMY_VIOLATION = "autonomy_violation"
    TRANSPARENCY_VIOLATION = "transparency_violation"
    ACCOUNTABILITY_VIOLATION = "accountability_violation"


@dataclass
class EthicalFinding:
    """Structured ethical finding."""
    principle: EthicalPrinciple
    violation_type: EthicalViolation
    severity: str
    description: str
    evidence: List[str]
    impact: str
    recommendations: List[str]


class EthicalAgent(ValidatorAgent):
    """
    Ethos-Guardian: Ethical validation agent for AI ethics and fairness.
    Reviews deployments for alignment with ethical principles and legal mandates.
    """
    
    def __init__(self, gemini_api, audit_logger, session, config=None):
        super().__init__("Ethos-Guardian", gemini_api, audit_logger, session, config)
        
        # Ethical principles mapping
        self.ethical_principles = {
            EthicalPrinciple.FAIRNESS: {
                "description": "Ensure fair treatment and avoid discrimination",
                "indicators": ["bias", "discrimination", "unfair treatment", "unequal access"]
            },
            EthicalPrinciple.TRANSPARENCY: {
                "description": "Ensure transparency in AI decision-making",
                "indicators": ["black box", "opaque", "unexplainable", "hidden logic"]
            },
            EthicalPrinciple.ACCOUNTABILITY: {
                "description": "Ensure accountability for AI decisions",
                "indicators": ["no accountability", "unclear responsibility", "blame shifting"]
            },
            EthicalPrinciple.PRIVACY: {
                "description": "Protect individual privacy and data rights",
                "indicators": ["privacy violation", "data misuse", "surveillance", "tracking"]
            },
            EthicalPrinciple.HUMAN_AUTONOMY: {
                "description": "Respect human autonomy and decision-making",
                "indicators": ["manipulation", "coercion", "deception", "autonomy violation"]
            }
        }
        
        # Legal frameworks
        self.legal_frameworks = {
            "GDPR": "General Data Protection Regulation",
            "CCPA": "California Consumer Privacy Act",
            "AI_ACT": "EU AI Act",
            "HUMAN_RIGHTS": "Universal Declaration of Human Rights"
        }
    
    def get_prompt_template(self) -> str:
        """Get the ethical validation prompt template."""
        return """
You are Ethos-Guardian, an ethical validation agent specializing in AI ethics, fairness, and rule-of-law compliance. Your mission is to review deployments for alignment with ethical principles and international legal mandates.

## Analysis Context:
- Deployment Context: {deployment_context}
- AI Components: {ai_components}
- Data Usage: {data_usage}
- Decision Impact: {decision_impact}

## Your Ethical Framework:

### 1. Fairness and Non-Discrimination
- **Bias Detection**: Identify potential biases in algorithms
- **Discrimination Prevention**: Ensure equal treatment for all groups
- **Equal Access**: Verify equal access to AI services
- **Representation**: Check for diverse representation in training data

### 2. Transparency and Explainability
- **Decision Transparency**: Ensure AI decisions are explainable
- **Process Transparency**: Make AI processes understandable
- **Data Transparency**: Provide clear information about data usage
- **Algorithm Transparency**: Disclose algorithm details where appropriate

### 3. Accountability and Responsibility
- **Clear Responsibility**: Define clear responsibility for AI decisions
- **Audit Trails**: Ensure comprehensive audit trails
- **Human Oversight**: Verify human oversight mechanisms
- **Redress Mechanisms**: Provide mechanisms for redress

### 4. Privacy and Data Protection
- **Data Minimization**: Ensure minimal data collection
- **Consent Management**: Verify proper consent mechanisms
- **Data Security**: Ensure data protection measures
- **Right to Erasure**: Support data deletion rights

### 5. Human Autonomy and Dignity
- **Human Control**: Ensure human control over AI systems
- **Autonomy Respect**: Respect human decision-making autonomy
- **Dignity Protection**: Protect human dignity and rights
- **Manipulation Prevention**: Prevent AI manipulation

### 6. Legal Compliance
- **Regulatory Compliance**: Ensure compliance with relevant regulations
- **International Law**: Verify compliance with international law
- **Human Rights**: Respect fundamental human rights
- **Ethical Standards**: Meet industry ethical standards

## Output Format:
Provide a comprehensive ethical analysis in the following JSON structure:

```json
{{
    "ethical_concerns": [
        {{
            "principle": "fairness|transparency|accountability|privacy|human_autonomy|non_maleficence|beneficence|justice",
            "violation_type": "bias|discrimination|privacy_violation|autonomy_violation|transparency_violation|accountability_violation",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "description": "Detailed ethical concern description",
            "evidence": ["evidence1", "evidence2"],
            "impact": "Description of potential impact",
            "recommendations": ["recommendation1", "recommendation2"]
        }}
    ],
    "legal_flags": [
        {{
            "framework": "GDPR|CCPA|AI_ACT|HUMAN_RIGHTS",
            "violation": "Specific legal violation",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "description": "Legal compliance issue description",
            "recommendations": ["legal_recommendation1", "legal_recommendation2"]
        }}
    ],
    "ethical_summary": {{
        "overall_ethical_status": "COMPLIANT|NON_COMPLIANT|PARTIAL",
        "critical_concerns": integer,
        "legal_violations": integer,
        "ethical_score": float (0.0-1.0)
    }},
    "recommendations": [
        "Priority ethical and legal recommendations"
    ]
}}
```

## Ethical Guidelines:
1. **Be principled** - Apply ethical principles consistently
2. **Be inclusive** - Consider impact on all stakeholders
3. **Be transparent** - Provide clear ethical reasoning
4. **Be accountable** - Take responsibility for ethical assessments
5. **Be forward-looking** - Consider long-term ethical implications
6. **Be legally compliant** - Ensure compliance with applicable laws

Analyze the provided deployment context for ethical and legal compliance.
"""
    
    async def validate(self, deployment_context: Dict[str, Any]) -> AgentResult:
        """
        Perform comprehensive ethical validation.
        
        Args:
            deployment_context: Deployment context to analyze
            
        Returns:
            AgentResult: Ethical validation result
        """
        try:
            # Prepare analysis context
            analysis_context = self._prepare_analysis_context(deployment_context)
            
            # Generate ethical validation prompt
            prompt = self.get_prompt_template().format(**analysis_context)
            
            # Call Gemini for analysis
            response = await self._call_gemini(prompt)
            
            # Parse and validate response
            result = self.parse_response(response)
            
            # Determine threat level
            result.threat_level = self._determine_threat_level(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Ethical validation failed: {e}")
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
        """Parse Gemini response into ethical validation result."""
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
            ethical_concerns = analysis_data.get("ethical_concerns", [])
            legal_flags = analysis_data.get("legal_flags", [])
            ethical_summary = analysis_data.get("ethical_summary", {})
            
            # Determine verdict based on ethical status
            overall_status = ethical_summary.get("overall_ethical_status", "NON_COMPLIANT")
            critical_concerns = ethical_summary.get("critical_concerns", 0)
            legal_violations = ethical_summary.get("legal_violations", 0)
            
            if critical_concerns > 0 or legal_violations > 0:
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
                "ethical_concerns": ethical_concerns,
                "legal_flags": legal_flags,
                "ethical_summary": ethical_summary,
                "recommendations": analysis_data.get("recommendations", []),
                "total_concerns": len(ethical_concerns),
                "critical_concerns": critical_concerns,
                "legal_violations": legal_violations
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
            self.logger.error(f"Failed to parse ethical response: {e}")
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
        """Prepare context for ethical analysis."""
        return {
            "deployment_context": json.dumps(deployment_context, indent=2),
            "ai_components": json.dumps(deployment_context.get("ai_components", []), indent=2),
            "data_usage": json.dumps(deployment_context.get("data_usage", {}), indent=2),
            "decision_impact": json.dumps(deployment_context.get("decision_impact", {}), indent=2)
        }
    
    def _calculate_confidence(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the ethical analysis."""
        base_confidence = 0.8
        
        # Increase confidence based on concern diversity
        ethical_concerns = analysis_data.get("ethical_concerns", [])
        if ethical_concerns:
            principles = set(concern.get("principle", "") for concern in ethical_concerns)
            if len(principles) > 3:
                base_confidence += 0.1
        
        # Increase confidence for detailed legal analysis
        legal_flags = analysis_data.get("legal_flags", [])
        if legal_flags:
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _determine_threat_level(self, result: AgentResult) -> ThreatLevel:
        """Determine threat level based on ethical findings."""
        critical_concerns = result.details.get("critical_concerns", 0)
        legal_violations = result.details.get("legal_violations", 0)
        
        if critical_concerns > 0 or legal_violations > 0:
            return ThreatLevel.CRITICAL
        else:
            return ThreatLevel.INFO
    
    def _calculate_reward(self, result: AgentResult) -> float:
        """Calculate RL reward for ethical agent performance."""
        base_reward = super()._calculate_reward(result)
        
        # Additional reward for ethical concern detection
        total_concerns = result.details.get("total_concerns", 0)
        if total_concerns > 0:
            base_reward += 0.2
        
        # Reward for critical concern detection
        critical_concerns = result.details.get("critical_concerns", 0)
        if critical_concerns > 0:
            base_reward += 0.3
        
        # Reward for legal compliance analysis
        legal_violations = result.details.get("legal_violations", 0)
        if legal_violations > 0:
            base_reward += 0.2
        
        return max(-1.0, min(1.0, base_reward))
