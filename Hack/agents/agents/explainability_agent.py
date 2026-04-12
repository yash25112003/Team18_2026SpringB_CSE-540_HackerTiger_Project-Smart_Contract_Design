"""
Explainability Agent (Lucid-Analyst) - Explains other agents' verdicts in plain language.
Provides audit and trust through clear explanations of validation rationale.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

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


@dataclass
class Explanation:
    """Structured explanation of agent verdict."""
    agent_name: str
    verdict: str
    explanation: str
    evidence: List[str]
    confidence: float
    recommendations: List[str]


class ExplainabilityAgent(ValidatorAgent):
    """
    Lucid-Analyst: Explainability agent that provides clear explanations of validation results.
    Enhances trust and auditability through plain language explanations.
    """
    
    def __init__(self, gemini_api, audit_logger, session, config=None):
        super().__init__("Lucid-Analyst", gemini_api, audit_logger, session, config)
        
        # Explanation templates
        self.explanation_templates = {
            "APPROVE": "The deployment has been approved because {reason}.",
            "REJECT": "The deployment has been rejected because {reason}.",
            "ISOLATE": "The deployment has been isolated because {reason}."
        }
    
    def get_prompt_template(self) -> str:
        """Get the explainability prompt template."""
        return """
You are Lucid-Analyst, an explainability agent that provides clear, plain language explanations of validation results. Your mission is to explain the rationale and evidence behind each agent's verdict in a way that is understandable to both technical and non-technical stakeholders.

## Analysis Context:
- Agent Results: {agent_results}
- Session ID: {session_id}
- Deployment Context: {deployment_context}

## Your Explanation Framework:

### 1. Clear Language Explanations
- **Plain English**: Use simple, clear language accessible to all stakeholders
- **Technical Accuracy**: Maintain technical accuracy while being accessible
- **Contextual Relevance**: Explain findings in business and technical context
- **Actionable Insights**: Provide specific, actionable recommendations

### 2. Evidence-Based Reasoning
- **Specific Evidence**: Cite specific data points and findings
- **Logical Flow**: Present reasoning in logical, step-by-step manner
- **Confidence Levels**: Explain confidence levels and uncertainty
- **Risk Assessment**: Clearly explain risk levels and implications

### 3. Stakeholder Communication
- **Executive Summary**: High-level summary for executives
- **Technical Details**: Detailed explanations for technical teams
- **Business Impact**: Clear explanation of business implications
- **Next Steps**: Specific recommendations for moving forward

### 4. Trust and Transparency
- **Transparency**: Be completely transparent about findings
- **Honesty**: Acknowledge limitations and uncertainties
- **Consistency**: Maintain consistent explanation standards
- **Accountability**: Take responsibility for explanations

## Output Format:
Provide comprehensive explanations in the following JSON structure:

```json
{{
    "explanations": [
        {{
            "agent_name": "agent_name",
            "verdict": "APPROVE|REJECT|ISOLATE",
            "explanation": "Clear, plain language explanation of the verdict",
            "evidence": ["evidence1", "evidence2"],
            "confidence": float (0.0-1.0),
            "recommendations": ["recommendation1", "recommendation2"]
        }}
    ],
    "executive_summary": {{
        "overall_status": "APPROVED|REJECTED|ISOLATED",
        "key_findings": ["finding1", "finding2"],
        "business_impact": "Description of business impact",
        "next_steps": ["step1", "step2"]
    }},
    "technical_summary": {{
        "detailed_findings": ["detailed_finding1", "detailed_finding2"],
        "technical_evidence": ["evidence1", "evidence2"],
        "recommendations": ["technical_recommendation1", "technical_recommendation2"]
    }}
}}
```

## Explanation Guidelines:
1. **Be clear** - Use simple, understandable language
2. **Be accurate** - Maintain technical accuracy and precision
3. **Be complete** - Cover all important aspects
4. **Be actionable** - Provide specific recommendations
5. **Be honest** - Acknowledge limitations and uncertainties
6. **Be consistent** - Maintain consistent explanation standards

Analyze the provided agent results and provide clear, comprehensive explanations.
"""
    
    async def validate(self, deployment_context: Dict[str, Any]) -> AgentResult:
        """
        Perform explainability analysis.
        
        Args:
            deployment_context: Deployment context to analyze
            
        Returns:
            AgentResult: Explainability analysis result
        """
        try:
            # Prepare analysis context
            analysis_context = self._prepare_analysis_context(deployment_context)
            
            # Generate explainability prompt
            prompt = self.get_prompt_template().format(**analysis_context)
            
            # Call Gemini for analysis
            response = await self._call_gemini(prompt)
            
            # Parse and validate response
            result = self.parse_response(response)
            
            # Determine threat level
            result.threat_level = self._determine_threat_level(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Explainability analysis failed: {e}")
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
        """Parse Gemini response into explainability analysis result."""
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
            explanations = analysis_data.get("explanations", [])
            executive_summary = analysis_data.get("executive_summary", {})
            technical_summary = analysis_data.get("technical_summary", {})
            
            # Determine verdict based on overall status
            overall_status = executive_summary.get("overall_status", "REJECTED")
            if overall_status == "APPROVED":
                verdict = "APPROVE"
            elif overall_status == "ISOLATED":
                verdict = "ISOLATE"
            else:
                verdict = "REJECT"
            
            # Calculate confidence
            confidence = self._calculate_confidence(analysis_data)
            
            # Prepare details
            details = {
                "explanations": explanations,
                "executive_summary": executive_summary,
                "technical_summary": technical_summary,
                "total_explanations": len(explanations)
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
            self.logger.error(f"Failed to parse explainability response: {e}")
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
        """Prepare context for explainability analysis."""
        # Get agent results from session
        agent_results = self.session.agent_results
        
        return {
            "agent_results": json.dumps(agent_results, indent=2),
            "session_id": self.session.session_id,
            "deployment_context": json.dumps(deployment_context, indent=2)
        }
    
    def _calculate_confidence(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the explainability analysis."""
        base_confidence = 0.8
        
        # Increase confidence based on explanation quality
        explanations = analysis_data.get("explanations", [])
        if explanations:
            # Check for detailed explanations
            detailed_explanations = sum(1 for exp in explanations 
                                      if len(exp.get("explanation", "")) > 100)
            if detailed_explanations > len(explanations) * 0.5:
                base_confidence += 0.1
        
        # Increase confidence for comprehensive summaries
        executive_summary = analysis_data.get("executive_summary", {})
        if executive_summary and executive_summary.get("key_findings"):
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _determine_threat_level(self, result: AgentResult) -> ThreatLevel:
        """Determine threat level based on explainability findings."""
        # Explainability agent typically doesn't identify threats directly
        # but can indicate high-risk situations based on explanations
        executive_summary = result.details.get("executive_summary", {})
        business_impact = executive_summary.get("business_impact", "").lower()
        
        if "critical" in business_impact or "severe" in business_impact:
            return ThreatLevel.HIGH
        elif "significant" in business_impact or "major" in business_impact:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.INFO
    
    def _calculate_reward(self, result: AgentResult) -> float:
        """Calculate RL reward for explainability agent performance."""
        base_reward = super()._calculate_reward(result)
        
        # Additional reward for comprehensive explanations
        total_explanations = result.details.get("total_explanations", 0)
        if total_explanations > 5:
            base_reward += 0.2
        
        # Reward for detailed summaries
        executive_summary = result.details.get("executive_summary", {})
        if executive_summary and len(executive_summary.get("key_findings", [])) > 3:
            base_reward += 0.1
        
        return max(-1.0, min(1.0, base_reward))
