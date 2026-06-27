"""
"""

import json
import asyncio
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class ThreatCategory(Enum):
    """Categories of threats for threat modeling."""
    EVASION = "evasion"
    MISUSE = "misuse"
    ADVERSARIAL_HARM = "adversarial_harm"
    DATA_POISONING = "data_poisoning"
    MODEL_EXTRACTION = "model_extraction"
    PRIVACY_ATTACKS = "privacy_attacks"
    PROMPT_INJECTION = "prompt_injection"
    BACKDOOR_ATTACKS = "backdoor_attacks"

class AttackerProfile(Enum):
    """Types of attacker profiles."""
    SCRIPT_KIDDIE = "script_kiddie"
    HACKTIVIST = "hacktivist"
    CRIMINAL = "criminal"
    NATION_STATE = "nation_state"
    INSIDER = "insider"

class ThreatModel:
    """Threat modeling utilities."""
    
    @staticmethod
    def assess_threat_landscape(deployment_context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the threat landscape for a deployment."""
        return {
            "threat_level": "HIGH",
            "attack_vectors": [],
            "risk_score": 0.8
        }




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

class ThreatModelAgent(ValidatorAgent):
    """
    Threat Model Agent: Models candidate against ML threat taxonomy.
    Uses Microsoft guidance for threat modeling and risk assessment.
    """
    
    def __init__(self, gemini_api, audit_logger, session, config=None):
        super().__init__("Threat-Model-Agent", gemini_api, audit_logger, session, config)
        
        # Threat taxonomy mapping
        self.threat_taxonomy = {
            ThreatCategory.EVASION: {
                "description": "Adversarial evasion attacks against ML models",
                "attack_vectors": ["adversarial_examples", "input_manipulation", "feature_evasion"],
                "mitigation": ["adversarial_training", "input_validation", "anomaly_detection"]
            },
            ThreatCategory.MISUSE: {
                "description": "Malicious misuse of AI systems",
                "attack_vectors": ["prompt_injection", "jailbreaking", "role_play"],
                "mitigation": ["content_filtering", "rate_limiting", "user_authentication"]
            },
            ThreatCategory.ADVERSARIAL_HARM: {
                "description": "Adversarial examples causing real-world harm",
                "attack_vectors": ["physical_adversarial", "sensor_manipulation", "perception_attacks"],
                "mitigation": ["robust_training", "sensor_fusion", "human_oversight"]
            },
            ThreatCategory.DATA_POISONING: {
                "description": "Training data manipulation attacks",
                "attack_vectors": ["backdoor_injection", "label_flipping", "feature_poisoning"],
                "mitigation": ["data_validation", "anomaly_detection", "differential_privacy"]
            },
            ThreatCategory.MODEL_EXTRACTION: {
                "description": "Model architecture and parameter theft",
                "attack_vectors": ["model_queries", "gradient_attacks", "membership_inference"],
                "mitigation": ["api_rate_limiting", "output_perturbation", "model_watermarking"]
            },
            ThreatCategory.PRIVACY_ATTACKS: {
                "description": "Privacy violation attacks",
                "attack_vectors": ["membership_inference", "attribute_inference", "model_inversion"],
                "mitigation": ["differential_privacy", "federated_learning", "data_anonymization"]
            },
            ThreatCategory.PROMPT_INJECTION: {
                "description": "LLM prompt manipulation attacks",
                "attack_vectors": ["instruction_override", "context_manipulation", "role_confusion"],
                "mitigation": ["prompt_engineering", "input_sanitization", "output_filtering"]
            },
            ThreatCategory.BACKDOOR_ATTACKS: {
                "description": "Hidden malicious functionality",
                "attack_vectors": ["trigger_activation", "covert_channels", "steganography"],
                "mitigation": ["model_verification", "behavioral_analysis", "adversarial_testing"]
            }
        }
        
        # Attacker profiles with skill, resources, motivation
        self.attacker_profiles = {
            AttackerProfile.SCRIPT_KIDDIE: {"skill": 1, "resources": 1, "motivation": 2},
            AttackerProfile.HACKTIVIST: {"skill": 3, "resources": 2, "motivation": 4},
            AttackerProfile.CRIMINAL: {"skill": 4, "resources": 3, "motivation": 5},
            AttackerProfile.NATION_STATE: {"skill": 5, "resources": 5, "motivation": 5},
            AttackerProfile.INSIDER: {"skill": 4, "resources": 4, "motivation": 3}
        }
    
    def get_prompt_template(self) -> str:
        """Get the threat modeling prompt template."""
        return """
You are Threat-Model-Agent, an advanced threat modeling specialist using Microsoft's ML threat taxonomy and methodologies. Your mission is to evaluate each deployment against the latest ML threat landscape, identify coverage gaps, and assess likely attacker profiles.

## Analysis Context:
- Deployment Context: {deployment_context}
- System Architecture: {system_architecture}
- Data Types: {data_types}
- AI/ML Components: {ai_components}
- Security Controls: {security_controls}

## Your Threat Modeling Framework:

### 1. ML Threat Taxonomy Analysis
Evaluate against Microsoft's ML threat categories:
- **Evasion**: Adversarial evasion attacks against ML models
- **Misuse**: Malicious misuse of AI systems
- **Adversarial Harm**: Adversarial examples causing real-world harm
- **Data Poisoning**: Training data manipulation attacks
- **Model Extraction**: Model architecture and parameter theft
- **Privacy Attacks**: Privacy violation attacks
- **Prompt Injection**: LLM prompt manipulation attacks
- **Backdoor Attacks**: Hidden malicious functionality

### 2. Attack Vector Analysis
For each applicable threat category:
- **Entry Points**: How attackers can access the system
- **Attack Paths**: Specific techniques and methods
- **Exploitation**: How vulnerabilities can be exploited
- **Impact**: Potential damage and consequences

### 3. Attacker Profile Assessment
Evaluate against different attacker types:
- **Script Kiddie**: Low skill, low resources, moderate motivation
- **Hacktivist**: Medium skill, low resources, high motivation
- **Criminal**: High skill, medium resources, very high motivation
- **Nation State**: Very high skill, very high resources, very high motivation
- **Insider**: High skill, high resources, medium motivation

### 4. Risk Assessment
- **Likelihood**: Probability of attack success
- **Impact**: Potential business and technical impact
- **Risk Score**: Combined likelihood and impact
- **Coverage Gaps**: Missing security controls
- **Control Effectiveness**: How well existing controls mitigate threats

### 5. Mitigation Strategies
- **Preventive Controls**: Stop attacks before they happen
- **Detective Controls**: Identify attacks in progress
- **Corrective Controls**: Respond to and recover from attacks
- **Compensating Controls**: Alternative security measures

## Output Format:
Provide a comprehensive threat model in the following JSON structure:

```json
{{
    "threat_assessments": [
        {{
            "threat_category": "evasion|misuse|adversarial_harm|data_poisoning|model_extraction|privacy_attacks|prompt_injection|backdoor_attacks",
            "likelihood": float (0.0-1.0),
            "impact": float (0.0-1.0),
            "risk_score": float (0.0-1.0),
            "description": "Detailed threat description",
            "attack_vectors": ["vector1", "vector2"],
            "mitigation_strategies": ["strategy1", "strategy2"],
            "attacker_profiles": ["profile1", "profile2"]
        }}
    ],
    "overall_risk_score": float (0.0-1.0),
    "coverage_gaps": [
        "Missing security controls or coverage areas"
    ],
    "recommended_controls": [
        "Priority security controls to implement"
    ],
    "attacker_landscape": {{
        "primary_threats": ["threat1", "threat2"],
        "likely_attackers": ["profile1", "profile2"],
        "attack_surface": "Assessment of attack surface",
        "defense_depth": "Assessment of defense in depth"
    }},
    "threat_model_summary": {{
        "total_threats": integer,
        "high_risk_threats": integer,
        "coverage_percentage": float,
        "recommended_priority": "HIGH|MEDIUM|LOW"
    }}
}}
```

## Threat Modeling Guidelines:
1. **Be comprehensive** - Consider all applicable threat categories
2. **Be realistic** - Focus on practical, likely threats
3. **Consider context** - Threats vary by deployment environment
4. **Prioritize impact** - Focus on high-impact threats first
5. **Provide mitigations** - Always suggest defensive measures
6. **Think like attackers** - Consider attacker motivations and capabilities

Analyze the provided deployment context against the ML threat taxonomy and provide a comprehensive threat model.
"""
    
    async def validate(self, deployment_context: Dict[str, Any]) -> AgentResult:
        """
        Perform comprehensive threat modeling validation.
        
        Args:
            deployment_context: Deployment context to analyze
            
        Returns:
            AgentResult: Threat modeling result
        """
        try:
            # Prepare analysis context
            analysis_context = self._prepare_analysis_context(deployment_context)
            
            # Generate threat modeling prompt
            prompt = self.get_prompt_template().format(**analysis_context)
            
            # Call Gemini for analysis
            response = await self._call_gemini(prompt)
            
            # Parse and validate response
            result = self.parse_response(response)
            
            # Perform additional threat landscape analysis
            threat_landscape = self._analyze_threat_landscape(deployment_context)
            
            # Merge results
            if threat_landscape:
                result.details["threat_landscape_analysis"] = threat_landscape
            
            # Determine threat level
            result.threat_level = self._determine_threat_level(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Threat modeling failed: {e}")
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
        """Parse Gemini response into threat modeling result."""
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
            threat_assessments = analysis_data.get("threat_assessments", [])
            overall_risk_score = analysis_data.get("overall_risk_score", 0.0)
            high_risk_threats = sum(1 for t in threat_assessments if t.get("risk_score", 0) >= 0.7)
            
            # Determine verdict based on risk score
            if overall_risk_score >= 0.8:
                verdict = "ISOLATE"
            elif overall_risk_score >= 0.6:
                verdict = "REJECT"
            elif overall_risk_score >= 0.4:
                verdict = "REJECT"
            else:
                verdict = "APPROVE"
            
            # Calculate confidence
            confidence = self._calculate_confidence(analysis_data)
            
            # Prepare details
            details = {
                "threat_assessments": threat_assessments,
                "overall_risk_score": overall_risk_score,
                "coverage_gaps": analysis_data.get("coverage_gaps", []),
                "recommended_controls": analysis_data.get("recommended_controls", []),
                "attacker_landscape": analysis_data.get("attacker_landscape", {}),
                "threat_model_summary": analysis_data.get("threat_model_summary", {}),
                "total_threats": len(threat_assessments),
                "high_risk_threats": high_risk_threats
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
            self.logger.error(f"Failed to parse threat model response: {e}")
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
        """Prepare context for threat modeling analysis."""
        return {
            "deployment_context": json.dumps(deployment_context, indent=2),
            "system_architecture": json.dumps(deployment_context.get("architecture", {}), indent=2),
            "data_types": json.dumps(deployment_context.get("data_types", []), indent=2),
            "ai_components": json.dumps(deployment_context.get("ai_components", []), indent=2),
            "security_controls": json.dumps(deployment_context.get("security_controls", {}), indent=2)
        }
    
    def _analyze_threat_landscape(self, deployment_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze threat landscape using built-in threat model."""
        return ThreatModel.assess_threat_landscape(deployment_context)
    
    def _calculate_confidence(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the threat modeling analysis."""
        base_confidence = 0.8
        
        # Increase confidence based on threat diversity
        threat_assessments = analysis_data.get("threat_assessments", [])
        if threat_assessments:
            threat_categories = set(t.get("threat_category", "") for t in threat_assessments)
            if len(threat_categories) > 4:
                base_confidence += 0.1
        
        # Increase confidence for detailed attacker landscape
        attacker_landscape = analysis_data.get("attacker_landscape", {})
        if attacker_landscape and attacker_landscape.get("primary_threats"):
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _determine_threat_level(self, result: AgentResult) -> ThreatLevel:
        """Determine threat level based on threat modeling results."""
        overall_risk_score = result.details.get("overall_risk_score", 0.0)
        high_risk_threats = result.details.get("high_risk_threats", 0)
        
        if overall_risk_score >= 0.8 or high_risk_threats >= 3:
            return ThreatLevel.CRITICAL
        elif overall_risk_score >= 0.6 or high_risk_threats >= 2:
            return ThreatLevel.HIGH
        elif overall_risk_score >= 0.4 or high_risk_threats >= 1:
            return ThreatLevel.MEDIUM
        elif overall_risk_score >= 0.2:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.INFO
    
    def _calculate_reward(self, result: AgentResult) -> float:
        """Calculate RL reward for threat modeling performance."""
        base_reward = super()._calculate_reward(result)
        
        # Additional reward for comprehensive threat coverage
        total_threats = result.details.get("total_threats", 0)
        if total_threats > 5:
            base_reward += 0.2
        
        # Reward for identifying high-risk threats
        high_risk_threats = result.details.get("high_risk_threats", 0)
        if high_risk_threats > 0:
            base_reward += 0.3
        
        # Reward for providing actionable recommendations
        recommended_controls = result.details.get("recommended_controls", [])
        if len(recommended_controls) > 3:
            base_reward += 0.1
        
        return max(-1.0, min(1.0, base_reward))
