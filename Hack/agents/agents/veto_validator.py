"""
Veto-Validator: Aggregates all agent outputs and enforces consensus.
Issues final verdict ('APPROVE', 'REJECT', 'ISOLATE') with session-aware consensus.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics

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
    from ..system_constitution import ThreatLevel, VerdictType, CONSTITUTION
except ImportError:
    # For standalone execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from system_constitution import ThreatLevel, VerdictType, CONSTITUTION


class ConsensusStatus(Enum):
    """Consensus status enumeration."""
    APPROVED = "approved"
    REJECTED = "rejected"
    ISOLATED = "isolated"
    INCONCLUSIVE = "inconclusive"


@dataclass
class ConsensusAnalysis:
    """Structured consensus analysis result."""
    total_agents: int
    approval_count: int
    rejection_count: int
    isolation_count: int
    consensus_score: float
    confidence: float
    critical_findings: List[Dict[str, Any]]
    risk_factors: List[str]


@dataclass
class FinalVerdict:
    """Final validation verdict with comprehensive analysis."""
    verdict: VerdictType
    consensus_analysis: ConsensusAnalysis
    agent_results: List[AgentResult]
    session_id: str
    timestamp: str
    ledger_block: Dict[str, Any]


class VetoValidator(ValidatorAgent):
    """
    Veto-Validator: Final consensus agent that aggregates all agent outputs.
    Enforces quorum, considers critical findings, and issues final verdict.
    """
    
    def __init__(self, gemini_api, audit_logger, session, config=None):
        super().__init__("Veto-Validator", gemini_api, audit_logger, session, config)
        
        # Consensus configuration
        self.quorum_threshold = CONSTITUTION.CONSENSUS_QUORUM_THRESHOLD
        self.minimum_agents = CONSTITUTION.MINIMUM_AGENTS_FOR_QUORUM
        self.critical_threat_threshold = CONSTITUTION.CRITICAL_THREAT_THRESHOLD
        
        # Verdict weights
        self.verdict_weights = {
            "ISOLATE": 3.0,
            "REJECT": 2.0,
            "APPROVE": 1.0
        }
        
        # Risk factors
        self.risk_factors = [
            "security_vulnerabilities",
            "adversarial_attacks",
            "anomaly_detections",
            "threat_model_violations",
            "compliance_violations",
            "authorization_failures",
            "performance_regressions"
        ]
    
    def get_prompt_template(self) -> str:
        """Get the consensus analysis prompt template."""
        return """
You are Veto-Validator, the final consensus agent responsible for aggregating all agent outputs and issuing the final verdict. Your mission is to analyze all agent results, apply consensus quorum, consider critical findings, and issue a final verdict for the immutable ledger.

## Analysis Context:
- Agent Results: {agent_results}
- Session ID: {session_id}
- Consensus Threshold: {quorum_threshold}
- Critical Threat Threshold: {critical_threat_threshold}

## Your Consensus Framework:

### 1. Agent Result Aggregation
- **Collect all agent results** from security, red team, anomaly, threat model, compliance, authorization, performance, and other agents
- **Analyze verdict distribution** across all agents
- **Calculate consensus metrics** including approval/rejection/isolation counts
- **Identify critical findings** that require immediate attention

### 2. Quorum Analysis
- **Check quorum requirements** based on system constitution
- **Calculate consensus score** as percentage of agreeing agents
- **Determine consensus status** (approved, rejected, isolated, inconclusive)
- **Validate minimum agent participation** for valid consensus

### 3. Critical Finding Analysis
- **Identify high-severity threats** that trigger isolation
- **Assess critical vulnerabilities** that require immediate action
- **Evaluate security violations** that compromise system integrity
- **Consider compliance failures** that violate regulatory requirements

### 4. Risk Assessment
- **Calculate overall risk score** based on all agent findings
- **Identify risk factors** contributing to the assessment
- **Assess business impact** of potential issues
- **Evaluate mitigation effectiveness** of proposed solutions

### 5. Final Verdict Logic
- **ISOLATE**: Critical threats, high-severity vulnerabilities, security violations
- **REJECT**: Non-critical issues, compliance failures, performance problems
- **APPROVE**: All agents approve, no critical issues, acceptable risk level

## Output Format:
Provide a comprehensive consensus analysis in the following JSON structure:

```json
{{
    "final_verdict": "APPROVE|REJECT|ISOLATE",
    "consensus_analysis": {{
        "total_agents": integer,
        "approval_count": integer,
        "rejection_count": integer,
        "isolation_count": integer,
        "consensus_score": float (0.0-1.0),
        "confidence": float (0.0-1.0),
        "critical_findings": [
            {{
                "agent": "agent_name",
                "finding": "description",
                "severity": "critical|high|medium|low",
                "impact": "business_impact_description"
            }}
        ],
        "risk_factors": ["factor1", "factor2"]
    }},
    "ledger_block": {{
        "session_id": "session_id",
        "timestamp": "ISO_timestamp",
        "verdict": "APPROVE|REJECT|ISOLATE",
        "consensus_score": float,
        "agent_results": [
            {{
                "agent_name": "name",
                "verdict": "APPROVE|REJECT|ISOLATE",
                "confidence": float,
                "threat_level": "CRITICAL|HIGH|MEDIUM|LOW|INFO"
            }}
        ],
        "critical_findings": ["finding1", "finding2"],
        "recommendations": ["recommendation1", "recommendation2"],
        "risk_score": float (0.0-10.0),
        "compliance_status": "COMPLIANT|NON_COMPLIANT|PARTIAL",
        "security_status": "SECURE|VULNERABLE|COMPROMISED"
    }}
}}
```

## Consensus Guidelines:
1. **Be decisive** - Make clear, unambiguous decisions
2. **Be fair** - Consider all agent inputs equally
3. **Be thorough** - Analyze all findings comprehensively
4. **Be consistent** - Apply consistent decision criteria
5. **Be transparent** - Provide clear reasoning for decisions
6. **Be accountable** - Ensure decisions are auditable and traceable

Analyze all agent results and issue the final consensus verdict.
"""
    
    async def validate(self, deployment_context: Dict[str, Any]) -> AgentResult:
        """
        Perform final consensus validation.
        
        Args:
            deployment_context: Deployment context (not used in final validation)
            
        Returns:
            AgentResult: Final consensus result
        """
        try:
            # Get all agent results from session
            agent_results = self.session.agent_results
            
            if not agent_results:
                return AgentResult(
                    agent_name=self.name,
                    session_id=self.session.session_id,
                    status=AgentStatus.FAILED,
                    verdict="REJECT",
                    confidence=0.0,
                    details={"error": "No agent results available for consensus"},
                    error="No agent results available"
                )
            
            # Prepare consensus analysis context
            analysis_context = self._prepare_consensus_context(agent_results)
            
            # Generate consensus analysis prompt
            prompt = self.get_prompt_template().format(**analysis_context)
            
            # Call Gemini for consensus analysis
            response = await self._call_gemini(prompt)
            
            # Parse and validate response
            result = self.parse_response(response)
            
            # Perform additional consensus calculations
            consensus_analysis = self._calculate_consensus(agent_results)
            
            # Merge results
            result.details["consensus_analysis"] = consensus_analysis
            
            # Determine final verdict
            final_verdict = self._determine_final_verdict(result, agent_results)
            result.verdict = final_verdict
            
            # Create ledger block
            ledger_block = self._create_ledger_block(result, agent_results)
            result.details["ledger_block"] = ledger_block
            
            return result
            
        except Exception as e:
            self.logger.error(f"Consensus validation failed: {e}")
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
        """Parse Gemini response into consensus analysis result."""
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
            final_verdict = analysis_data.get("final_verdict", "REJECT")
            consensus_analysis = analysis_data.get("consensus_analysis", {})
            ledger_block = analysis_data.get("ledger_block", {})
            
            # Calculate confidence
            confidence = self._calculate_confidence(analysis_data)
            
            # Prepare details
            details = {
                "final_verdict": final_verdict,
                "consensus_analysis": consensus_analysis,
                "ledger_block": ledger_block,
                "total_agents": consensus_analysis.get("total_agents", 0),
                "consensus_score": consensus_analysis.get("consensus_score", 0.0),
                "critical_findings": consensus_analysis.get("critical_findings", [])
            }
            
            return AgentResult(
                agent_name=self.name,
                session_id=self.session.session_id,
                status=AgentStatus.COMPLETED,
                verdict=final_verdict,
                confidence=confidence,
                details=details
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse consensus response: {e}")
            return AgentResult(
                agent_name=self.name,
                session_id=self.session.session_id,
                status=AgentStatus.FAILED,
                verdict="REJECT",
                confidence=0.0,
                details={"error": f"Parse error: {str(e)}"},
                error=str(e)
            )
    
    def _prepare_consensus_context(self, agent_results: Dict[str, Any]) -> Dict[str, str]:
        """Prepare context for consensus analysis."""
        return {
            "agent_results": json.dumps(agent_results, indent=2),
            "session_id": self.session.session_id,
            "quorum_threshold": str(self.quorum_threshold),
            "critical_threat_threshold": str(self.critical_threat_threshold)
        }
    
    def _calculate_consensus(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate consensus metrics from agent results."""
        total_agents = len(agent_results)
        approval_count = sum(1 for result in agent_results.values() if result.get("verdict") == "APPROVE")
        rejection_count = sum(1 for result in agent_results.values() if result.get("verdict") == "REJECT")
        isolation_count = sum(1 for result in agent_results.values() if result.get("verdict") == "ISOLATE")
        
        # Calculate consensus score
        if total_agents > 0:
            consensus_score = approval_count / total_agents
        else:
            consensus_score = 0.0
        
        # Calculate confidence
        confidence = self._calculate_consensus_confidence(agent_results)
        
        # Identify critical findings
        critical_findings = []
        for agent_name, result in agent_results.items():
            if result.get("threat_level") == "CRITICAL":
                critical_findings.append({
                    "agent": agent_name,
                    "finding": result.get("details", {}).get("error", "Critical threat detected"),
                    "severity": "critical",
                    "impact": "High business impact"
                })
        
        return {
            "total_agents": total_agents,
            "approval_count": approval_count,
            "rejection_count": rejection_count,
            "isolation_count": isolation_count,
            "consensus_score": consensus_score,
            "confidence": confidence,
            "critical_findings": critical_findings
        }
    
    def _calculate_consensus_confidence(self, agent_results: Dict[str, Any]) -> float:
        """Calculate confidence in the consensus decision."""
        if not agent_results:
            return 0.0
        
        # Calculate average confidence of all agents
        confidences = [result.get("confidence", 0.0) for result in agent_results.values()]
        avg_confidence = statistics.mean(confidences) if confidences else 0.0
        
        # Adjust based on consensus agreement
        verdicts = [result.get("verdict", "REJECT") for result in agent_results.values()]
        verdict_counts = {}
        for verdict in verdicts:
            verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
        
        max_count = max(verdict_counts.values()) if verdict_counts else 0
        agreement_ratio = max_count / len(verdicts) if verdicts else 0
        
        # Combine average confidence with agreement ratio
        consensus_confidence = (avg_confidence + agreement_ratio) / 2
        
        return min(1.0, consensus_confidence)
    
    def _determine_final_verdict(self, result: AgentResult, agent_results: Dict[str, Any]) -> str:
        """Determine final verdict based on consensus analysis."""
        consensus_analysis = result.details.get("consensus_analysis", {})
        critical_findings = consensus_analysis.get("critical_findings", [])
        consensus_score = consensus_analysis.get("consensus_score", 0.0)
        
        # Check for critical findings that require isolation
        if critical_findings:
            return "ISOLATE"
        
        # Check for high-severity threats
        high_threat_agents = sum(1 for result in agent_results.values() 
                                if result.get("threat_level") in ["CRITICAL", "HIGH"])
        if high_threat_agents > 0:
            return "ISOLATE"
        
        # Check consensus threshold
        if consensus_score >= self.quorum_threshold:
            return "APPROVE"
        else:
            return "REJECT"
    
    def _create_ledger_block(self, result: AgentResult, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create immutable ledger block for the validation session."""
        from datetime import datetime
        
        return {
            "session_id": self.session.session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "verdict": result.verdict,
            "consensus_score": result.details.get("consensus_score", 0.0),
            "agent_results": [
                {
                    "agent_name": agent_name,
                    "verdict": agent_result.get("verdict", "REJECT"),
                    "confidence": agent_result.get("confidence", 0.0),
                    "threat_level": agent_result.get("threat_level", "INFO")
                }
                for agent_name, agent_result in agent_results.items()
            ],
            "critical_findings": result.details.get("consensus_analysis", {}).get("critical_findings", []),
            "recommendations": result.details.get("recommendations", []),
            "risk_score": self._calculate_risk_score(agent_results),
            "compliance_status": self._assess_compliance_status(agent_results),
            "security_status": self._assess_security_status(agent_results)
        }
    
    def _calculate_risk_score(self, agent_results: Dict[str, Any]) -> float:
        """Calculate overall risk score from agent results."""
        if not agent_results:
            return 0.0
        
        # Calculate weighted risk score based on threat levels
        threat_weights = {"CRITICAL": 5, "HIGH": 4, "MEDIUM": 3, "LOW": 2, "INFO": 1}
        total_weight = 0
        weighted_sum = 0
        
        for result in agent_results.values():
            threat_level = result.get("threat_level", "INFO")
            weight = threat_weights.get(threat_level, 1)
            total_weight += weight
            weighted_sum += weight * result.get("confidence", 0.0)
        
        if total_weight == 0:
            return 0.0
        
        risk_score = (weighted_sum / total_weight) * 2  # Scale to 0-10
        return min(10.0, risk_score)
    
    def _assess_compliance_status(self, agent_results: Dict[str, Any]) -> str:
        """Assess overall compliance status."""
        compliance_results = [result for result in agent_results.values() 
                            if "compliance" in result.get("agent_name", "").lower()]
        
        if not compliance_results:
            return "UNKNOWN"
        
        non_compliant = sum(1 for result in compliance_results 
                           if result.get("verdict") == "REJECT")
        
        if non_compliant == 0:
            return "COMPLIANT"
        elif non_compliant < len(compliance_results):
            return "PARTIAL"
        else:
            return "NON_COMPLIANT"
    
    def _assess_security_status(self, agent_results: Dict[str, Any]) -> str:
        """Assess overall security status."""
        security_results = [result for result in agent_results.values() 
                          if any(keyword in result.get("agent_name", "").lower() 
                                for keyword in ["security", "red", "threat", "anomaly"])]
        
        if not security_results:
            return "UNKNOWN"
        
        critical_threats = sum(1 for result in security_results 
                              if result.get("threat_level") == "CRITICAL")
        high_threats = sum(1 for result in security_results 
                          if result.get("threat_level") == "HIGH")
        
        if critical_threats > 0:
            return "COMPROMISED"
        elif high_threats > 0:
            return "VULNERABLE"
        else:
            return "SECURE"
    
    def _calculate_confidence(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the consensus analysis."""
        base_confidence = 0.9  # High confidence for consensus decisions
        
        # Increase confidence based on consensus agreement
        consensus_analysis = analysis_data.get("consensus_analysis", {})
        consensus_score = consensus_analysis.get("consensus_score", 0.0)
        if consensus_score > 0.8:
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _determine_threat_level(self, result: AgentResult) -> ThreatLevel:
        """Determine threat level based on consensus results."""
        critical_findings = result.details.get("consensus_analysis", {}).get("critical_findings", [])
        
        if critical_findings:
            return ThreatLevel.CRITICAL
        else:
            return ThreatLevel.INFO
    
    def _calculate_reward(self, result: AgentResult) -> float:
        """Calculate RL reward for consensus agent performance."""
        base_reward = super()._calculate_reward(result)
        
        # Additional reward for clear consensus decisions
        consensus_score = result.details.get("consensus_score", 0.0)
        if consensus_score > 0.8:
            base_reward += 0.2
        
        # Reward for identifying critical findings
        critical_findings = result.details.get("consensus_analysis", {}).get("critical_findings", [])
        if critical_findings:
            base_reward += 0.3
        
        return max(-1.0, min(1.0, base_reward))
