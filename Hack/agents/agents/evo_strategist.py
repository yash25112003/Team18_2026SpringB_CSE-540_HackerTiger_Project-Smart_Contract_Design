"""
Evolutionary Optimizer Agent (Evo-Strategist) - Optimizes validation parameters.
Analyzes historical outcomes and recommends mutations/improvements for validation rules and parameters.
"""

import json
import random
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


class OptimizationTarget(Enum):
    """Targets for optimization."""
    ACCURACY = "accuracy"
    SPEED = "speed"
    EFFICIENCY = "efficiency"
    RELIABILITY = "reliability"
    COST = "cost"


@dataclass
class OptimizationMutation:
    """Structured optimization mutation."""
    target: OptimizationTarget
    parameter: str
    current_value: Any
    proposed_value: Any
    expected_improvement: float
    confidence: float
    description: str


class EvoStrategist(ValidatorAgent):
    """
    Evo-Strategist: Evolutionary optimizer agent for validation parameters.
    Analyzes historical outcomes and recommends improvements for validation rules.
    """
    
    def __init__(self, gemini_api, audit_logger, session, config=None):
        super().__init__("Evo-Strategist", gemini_api, audit_logger, session, config)
        
        # Optimization parameters
        self.optimization_parameters = {
            "consensus_threshold": {"min": 0.5, "max": 0.9, "current": 0.75},
            "confidence_threshold": {"min": 0.3, "max": 0.9, "current": 0.7},
            "timeout_seconds": {"min": 30, "max": 300, "current": 60},
            "max_retries": {"min": 1, "max": 5, "current": 3},
            "batch_size": {"min": 1, "max": 20, "current": 5}
        }
        
        # Performance metrics
        self.performance_metrics = {
            "accuracy": 0.0,
            "speed": 0.0,
            "efficiency": 0.0,
            "reliability": 0.0,
            "cost": 0.0
        }
    
    def get_prompt_template(self) -> str:
        """Get the evolutionary optimization prompt template."""
        return """
You are Evo-Strategist, an evolutionary optimizer agent specializing in validation parameter optimization. Your mission is to analyze historical outcomes and recommend mutations/improvements for validation rules and parameters.

## Analysis Context:
- Historical Outcomes: {historical_outcomes}
- Current Parameters: {current_parameters}
- Performance Metrics: {performance_metrics}
- Optimization Goals: {optimization_goals}

## Your Optimization Framework:

### 1. Performance Analysis
- **Accuracy Metrics**: Analyze validation accuracy and precision
- **Speed Metrics**: Evaluate validation speed and latency
- **Efficiency Metrics**: Assess resource utilization and efficiency
- **Reliability Metrics**: Measure system reliability and stability
- **Cost Metrics**: Evaluate operational costs and resource usage

### 2. Parameter Optimization
- **Threshold Tuning**: Optimize decision thresholds
- **Timeout Optimization**: Adjust timeout parameters
- **Retry Logic**: Optimize retry mechanisms
- **Batch Processing**: Optimize batch sizes and processing
- **Resource Allocation**: Optimize resource allocation

### 3. Evolutionary Strategies
- **Mutation Strategies**: Propose parameter mutations
- **Crossover Strategies**: Combine successful parameters
- **Selection Strategies**: Select best-performing parameters
- **Adaptation Strategies**: Adapt to changing conditions
- **Learning Strategies**: Learn from historical data

### 4. Improvement Recommendations
- **Parameter Adjustments**: Specific parameter recommendations
- **Algorithm Improvements**: Algorithm optimization suggestions
- **Process Improvements**: Process optimization recommendations
- **Resource Optimization**: Resource usage optimization
- **Performance Tuning**: Performance optimization suggestions

## Output Format:
Provide a comprehensive optimization analysis in the following JSON structure:

```json
{{
    "proposed_mutations": [
        {{
            "target": "accuracy|speed|efficiency|reliability|cost",
            "parameter": "parameter_name",
            "current_value": "current_value",
            "proposed_value": "proposed_value",
            "expected_improvement": float (0.0-1.0),
            "confidence": float (0.0-1.0),
            "description": "Detailed mutation description"
        }}
    ],
    "optimization_summary": {{
        "total_mutations": integer,
        "high_confidence_mutations": integer,
        "expected_improvements": {{
            "accuracy": float,
            "speed": float,
            "efficiency": float,
            "reliability": float,
            "cost": float
        }},
        "optimization_priority": "HIGH|MEDIUM|LOW"
    }},
    "recommendations": [
        "Priority optimization recommendations"
    ]
}}
```

## Optimization Guidelines:
1. **Be data-driven** - Base recommendations on historical data
2. **Be incremental** - Propose gradual improvements
3. **Be measurable** - Ensure improvements are measurable
4. **Be realistic** - Propose achievable optimizations
5. **Be balanced** - Consider trade-offs between metrics
6. **Be adaptive** - Adapt to changing conditions

Analyze the provided historical data and propose optimization improvements.
"""
    
    async def validate(self, deployment_context: Dict[str, Any]) -> AgentResult:
        """
        Perform evolutionary optimization analysis.
        
        Args:
            deployment_context: Deployment context to analyze
            
        Returns:
            AgentResult: Optimization analysis result
        """
        try:
            # Prepare analysis context
            analysis_context = self._prepare_analysis_context(deployment_context)
            
            # Generate optimization prompt
            prompt = self.get_prompt_template().format(**analysis_context)
            
            # Call Gemini for analysis
            response = await self._call_gemini(prompt)
            
            # Parse and validate response
            result = self.parse_response(response)
            
            # Perform additional optimization calculations
            additional_mutations = self._generate_additional_mutations()
            
            # Merge results
            if additional_mutations:
                result.details["additional_mutations"] = additional_mutations
            
            # Determine threat level
            result.threat_level = self._determine_threat_level(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Evolutionary optimization failed: {e}")
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
        """Parse Gemini response into optimization analysis result."""
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
            proposed_mutations = analysis_data.get("proposed_mutations", [])
            optimization_summary = analysis_data.get("optimization_summary", {})
            
            # Determine verdict based on optimization potential
            high_confidence_mutations = optimization_summary.get("high_confidence_mutations", 0)
            expected_improvements = optimization_summary.get("expected_improvements", {})
            
            if high_confidence_mutations > 3:
                verdict = "APPROVE"
            elif high_confidence_mutations > 0:
                verdict = "APPROVE"
            else:
                verdict = "REJECT"
            
            # Calculate confidence
            confidence = self._calculate_confidence(analysis_data)
            
            # Prepare details
            details = {
                "proposed_mutations": proposed_mutations,
                "optimization_summary": optimization_summary,
                "recommendations": analysis_data.get("recommendations", []),
                "total_mutations": len(proposed_mutations),
                "high_confidence_mutations": high_confidence_mutations,
                "expected_improvements": expected_improvements
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
            self.logger.error(f"Failed to parse optimization response: {e}")
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
        """Prepare context for optimization analysis."""
        return {
            "historical_outcomes": json.dumps(deployment_context.get("historical_outcomes", {}), indent=2),
            "current_parameters": json.dumps(self.optimization_parameters, indent=2),
            "performance_metrics": json.dumps(self.performance_metrics, indent=2),
            "optimization_goals": json.dumps(deployment_context.get("optimization_goals", {}), indent=2)
        }
    
    def _generate_additional_mutations(self) -> List[Dict[str, Any]]:
        """Generate additional optimization mutations."""
        mutations = []
        
        # Generate mutations for each parameter
        for param_name, param_config in self.optimization_parameters.items():
            current_value = param_config["current"]
            min_value = param_config["min"]
            max_value = param_config["max"]
            
            # Generate random mutation
            if isinstance(current_value, (int, float)):
                mutation_range = (max_value - min_value) * 0.1  # 10% of range
                proposed_value = current_value + random.uniform(-mutation_range, mutation_range)
                proposed_value = max(min_value, min(max_value, proposed_value))
                
                mutations.append({
                    "target": "efficiency",
                    "parameter": param_name,
                    "current_value": current_value,
                    "proposed_value": proposed_value,
                    "expected_improvement": random.uniform(0.1, 0.3),
                    "confidence": random.uniform(0.6, 0.9),
                    "description": f"Optimize {param_name} for better efficiency"
                })
        
        return mutations
    
    def _calculate_confidence(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the optimization analysis."""
        base_confidence = 0.7
        
        # Increase confidence based on mutation quality
        proposed_mutations = analysis_data.get("proposed_mutations", [])
        if proposed_mutations:
            high_confidence_mutations = sum(1 for m in proposed_mutations 
                                          if m.get("confidence", 0) > 0.8)
            if high_confidence_mutations > len(proposed_mutations) * 0.5:
                base_confidence += 0.1
        
        # Increase confidence for detailed optimization summary
        optimization_summary = analysis_data.get("optimization_summary", {})
        if optimization_summary and optimization_summary.get("expected_improvements"):
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _determine_threat_level(self, result: AgentResult) -> ThreatLevel:
        """Determine threat level based on optimization findings."""
        # Optimization agent typically doesn't identify threats
        # but can indicate optimization opportunities
        high_confidence_mutations = result.details.get("high_confidence_mutations", 0)
        
        if high_confidence_mutations > 5:
            return ThreatLevel.LOW  # High optimization potential
        else:
            return ThreatLevel.INFO
    
    def _calculate_reward(self, result: AgentResult) -> float:
        """Calculate RL reward for evolutionary optimizer performance."""
        base_reward = super()._calculate_reward(result)
        
        # Additional reward for optimization mutations
        total_mutations = result.details.get("total_mutations", 0)
        if total_mutations > 0:
            base_reward += 0.2
        
        # Reward for high-confidence mutations
        high_confidence_mutations = result.details.get("high_confidence_mutations", 0)
        if high_confidence_mutations > 0:
            base_reward += 0.3
        
        # Reward for expected improvements
        expected_improvements = result.details.get("expected_improvements", {})
        if expected_improvements:
            total_improvement = sum(expected_improvements.values())
            if total_improvement > 0.5:
                base_reward += 0.2
        
        return max(-1.0, min(1.0, base_reward))
