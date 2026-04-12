"""
Performance Agent (Perf-Maestro) - Benchmarks and checks for regressions.
Analyzes canary deployment telemetry against baseline and flags significant regressions.
"""

import json
import statistics
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


class PerformanceMetric(Enum):
    """Performance metrics to monitor."""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    ERROR_RATE = "error_rate"
    LATENCY = "latency"
    AVAILABILITY = "availability"


class RegressionSeverity(Enum):
    """Regression severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class PerformanceRegression:
    """Structured performance regression finding."""
    metric: PerformanceMetric
    severity: RegressionSeverity
    baseline_value: float
    current_value: float
    regression_percentage: float
    description: str
    impact: str
    recommendations: List[str]


@dataclass
class PerformanceReport:
    """Comprehensive performance analysis report."""
    total_metrics: int
    regressions_found: int
    critical_regressions: int
    performance_score: float
    regressions: List[PerformanceRegression]
    recommendations: List[str]


class PerformanceAgent(ValidatorAgent):
    """
    Perf-Maestro: Performance validation agent for benchmarking and regression detection.
    Analyzes canary deployment telemetry against baseline and flags significant regressions.
    """
    
    def __init__(self, gemini_api, audit_logger, session, config=None):
        super().__init__("Perf-Maestro", gemini_api, audit_logger, session, config)
        
        # Performance thresholds
        self.performance_thresholds = {
            PerformanceMetric.RESPONSE_TIME.value: {"critical": 2.0, "high": 1.5, "medium": 1.2},
            PerformanceMetric.THROUGHPUT.value: {"critical": 0.5, "high": 0.7, "medium": 0.8},
            PerformanceMetric.CPU_USAGE.value: {"critical": 0.9, "high": 0.8, "medium": 0.7},
            PerformanceMetric.MEMORY_USAGE.value: {"critical": 0.9, "high": 0.8, "medium": 0.7},
            PerformanceMetric.ERROR_RATE.value: {"critical": 0.1, "high": 0.05, "medium": 0.02},
            PerformanceMetric.LATENCY.value: {"critical": 1.0, "high": 0.5, "medium": 0.2},
            PerformanceMetric.AVAILABILITY.value: {"critical": 0.95, "high": 0.98, "medium": 0.99}
        }
        
        # Baseline performance metrics
        self.baseline_metrics = {
            PerformanceMetric.RESPONSE_TIME.value: {"mean": 0.1, "std": 0.02, "p95": 0.2},
            PerformanceMetric.THROUGHPUT.value: {"mean": 1000, "std": 100, "p95": 1200},
            PerformanceMetric.CPU_USAGE.value: {"mean": 0.3, "std": 0.1, "p95": 0.5},
            PerformanceMetric.MEMORY_USAGE.value: {"mean": 0.4, "std": 0.1, "p95": 0.6},
            PerformanceMetric.ERROR_RATE.value: {"mean": 0.001, "std": 0.0005, "p95": 0.005},
            PerformanceMetric.LATENCY.value: {"mean": 0.05, "std": 0.01, "p95": 0.1},
            PerformanceMetric.AVAILABILITY.value: {"mean": 0.999, "std": 0.001, "p95": 0.9995}
        }
    
    def get_prompt_template(self) -> str:
        """Get the performance validation prompt template."""
        return """
You are Perf-Maestro, a performance validation agent specializing in benchmarking and regression detection. Your mission is to analyze canary deployment telemetry against baseline and flag significant performance regressions.

## Analysis Context:
- Deployment Context: {deployment_context}
- Telemetry Data: {telemetry_data}
- Baseline Metrics: {baseline_metrics}
- Performance Thresholds: {performance_thresholds}

## Your Performance Framework:

### 1. Performance Metrics Analysis
Monitor key performance indicators:
- **Response Time**: API and service response times
- **Throughput**: Requests per second, transactions per second
- **Resource Usage**: CPU, memory, disk, network utilization
- **Error Rates**: Application and system error rates
- **Latency**: Network and processing latency
- **Availability**: System uptime and availability

### 2. Regression Detection
Identify performance regressions:
- **Statistical Analysis**: Compare current vs baseline using statistical methods
- **Threshold Analysis**: Check against predefined performance thresholds
- **Trend Analysis**: Identify gradual performance degradation
- **Anomaly Detection**: Find unexpected performance patterns

### 3. Impact Assessment
Evaluate regression impact:
- **User Experience**: Impact on end-user experience
- **Business Impact**: Effect on business operations
- **System Stability**: Risk to system stability
- **Scalability**: Impact on system scalability

### 4. Root Cause Analysis
Investigate regression causes:
- **Code Changes**: Impact of recent code changes
- **Configuration Changes**: Effect of configuration modifications
- **Infrastructure Changes**: Impact of infrastructure updates
- **External Factors**: External dependencies and services

### 5. Optimization Recommendations
Provide performance optimization suggestions:
- **Code Optimization**: Code-level performance improvements
- **Configuration Tuning**: System configuration optimizations
- **Infrastructure Scaling**: Infrastructure scaling recommendations
- **Monitoring Enhancements**: Improved performance monitoring

## Output Format:
Provide a comprehensive performance analysis in the following JSON structure:

```json
{{
    "performance_report": {{
        "total_metrics": integer,
        "regressions_found": integer,
        "critical_regressions": integer,
        "performance_score": float (0.0-1.0)
    }},
    "regressions": [
        {{
            "metric": "response_time|throughput|cpu_usage|memory_usage|error_rate|latency|availability",
            "severity": "critical|high|medium|low|info",
            "baseline_value": float,
            "current_value": float,
            "regression_percentage": float,
            "description": "Detailed regression description",
            "impact": "Description of regression impact",
            "recommendations": ["recommendation1", "recommendation2"]
        }}
    ],
    "recommendations": [
        "Priority performance optimization recommendations"
    ],
    "performance_summary": {{
        "overall_status": "PASS|FAIL|WARNING",
        "critical_issues": integer,
        "performance_trend": "improving|stable|degrading",
        "optimization_priority": "HIGH|MEDIUM|LOW"
    }}
}}
```

## Performance Guidelines:
1. **Be precise** - Use accurate performance measurements
2. **Be comparative** - Always compare against established baselines
3. **Be contextual** - Consider deployment environment and use case
4. **Be actionable** - Provide specific optimization recommendations
5. **Be comprehensive** - Cover all relevant performance aspects
6. **Be realistic** - Focus on practical performance improvements

Analyze the provided telemetry data for performance regressions and optimization opportunities.
"""
    
    async def validate(self, deployment_context: Dict[str, Any]) -> AgentResult:
        """
        Perform comprehensive performance validation.
        
        Args:
            deployment_context: Deployment context to analyze
            
        Returns:
            AgentResult: Performance validation result
        """
        try:
            # Prepare analysis context
            analysis_context = self._prepare_analysis_context(deployment_context)
            
            # Generate performance validation prompt
            prompt = self.get_prompt_template().format(**analysis_context)
            
            # Call Gemini for analysis
            response = await self._call_gemini(prompt)
            
            # Parse and validate response
            result = self.parse_response(response)
            
            # Perform additional statistical analysis
            statistical_analysis = self._perform_statistical_analysis(deployment_context)
            
            # Merge results
            if statistical_analysis:
                result.details["statistical_analysis"] = statistical_analysis
            
            # Determine threat level
            result.threat_level = self._determine_threat_level(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Performance validation failed: {e}")
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
        """Parse Gemini response into performance validation result."""
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
            performance_report = analysis_data.get("performance_report", {})
            regressions = analysis_data.get("regressions", [])
            performance_summary = analysis_data.get("performance_summary", {})
            
            # Determine verdict based on performance status
            overall_status = performance_summary.get("overall_status", "FAIL")
            critical_issues = performance_summary.get("critical_issues", 0)
            
            if critical_issues > 0:
                verdict = "ISOLATE"
            elif overall_status == "FAIL":
                verdict = "REJECT"
            elif overall_status == "WARNING":
                verdict = "REJECT"
            else:
                verdict = "APPROVE"
            
            # Calculate confidence
            confidence = self._calculate_confidence(analysis_data)
            
            # Prepare details
            details = {
                "performance_report": performance_report,
                "regressions": regressions,
                "recommendations": analysis_data.get("recommendations", []),
                "performance_summary": performance_summary,
                "total_regressions": len(regressions),
                "critical_regressions": sum(1 for r in regressions if r.get("severity") == "critical")
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
            self.logger.error(f"Failed to parse performance response: {e}")
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
        """Prepare context for performance analysis."""
        # Generate synthetic telemetry data if not provided
        telemetry_data = deployment_context.get("telemetry_data", self._generate_synthetic_telemetry())
        
        # Convert performance thresholds to string keys for JSON serialization
        thresholds_serializable = {
            k.value if isinstance(k, Enum) else k: v 
            for k, v in self.performance_thresholds.items()
        }
        
        return {
            "deployment_context": json.dumps(deployment_context, indent=2),
            "telemetry_data": json.dumps(telemetry_data, indent=2),
            "baseline_metrics": json.dumps(self.baseline_metrics, indent=2),
            "performance_thresholds": json.dumps(thresholds_serializable, indent=2)
        }
    
    def _generate_synthetic_telemetry(self) -> Dict[str, Any]:
        """Generate synthetic telemetry data for analysis."""
        import random
        
        # Generate telemetry with some performance regressions
        telemetry = {
            "response_time": [random.uniform(0.08, 0.15) for _ in range(100)],
            "throughput": [random.uniform(900, 1100) for _ in range(100)],
            "cpu_usage": [random.uniform(0.25, 0.45) for _ in range(100)],
            "memory_usage": [random.uniform(0.35, 0.55) for _ in range(100)],
            "error_rate": [random.uniform(0.0005, 0.002) for _ in range(100)],
            "latency": [random.uniform(0.03, 0.08) for _ in range(100)],
            "availability": [random.uniform(0.998, 0.999) for _ in range(100)]
        }
        
        # Inject some performance regressions
        if random.random() < 0.4:  # 40% chance of regressions
            # Response time regression
            telemetry["response_time"][50:60] = [random.uniform(0.2, 0.4) for _ in range(10)]
            # CPU usage regression
            telemetry["cpu_usage"][70:80] = [random.uniform(0.7, 0.9) for _ in range(10)]
        
        return telemetry
    
    def _perform_statistical_analysis(self, deployment_context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform statistical analysis of performance metrics."""
        telemetry_data = deployment_context.get("telemetry_data", self._generate_synthetic_telemetry())
        
        analysis_results = {}
        
        for metric_name, values in telemetry_data.items():
            if isinstance(values, list) and len(values) > 10:
                baseline = self.baseline_metrics.get(metric_name, {"mean": 0.5, "std": 0.1})
                
                # Calculate statistics
                current_mean = statistics.mean(values)
                current_std = statistics.stdev(values) if len(values) > 1 else 0
                baseline_mean = baseline["mean"]
                baseline_std = baseline["std"]
                
                # Calculate regression percentage
                regression_pct = ((current_mean - baseline_mean) / baseline_mean) * 100
                
                # Determine severity
                severity = "info"
                if abs(regression_pct) > 50:
                    severity = "critical"
                elif abs(regression_pct) > 25:
                    severity = "high"
                elif abs(regression_pct) > 10:
                    severity = "medium"
                elif abs(regression_pct) > 5:
                    severity = "low"
                
                analysis_results[metric_name] = {
                    "current_mean": current_mean,
                    "baseline_mean": baseline_mean,
                    "regression_percentage": regression_pct,
                    "severity": severity,
                    "statistical_significance": abs(regression_pct) > 10
                }
        
        return analysis_results
    
    def _calculate_confidence(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the performance analysis."""
        base_confidence = 0.8
        
        # Increase confidence based on regression diversity
        regressions = analysis_data.get("regressions", [])
        if regressions:
            metric_types = set(r.get("metric", "") for r in regressions)
            if len(metric_types) > 3:
                base_confidence += 0.1
        
        # Increase confidence for detailed analysis
        performance_summary = analysis_data.get("performance_summary", {})
        if performance_summary and performance_summary.get("performance_trend"):
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _determine_threat_level(self, result: AgentResult) -> ThreatLevel:
        """Determine threat level based on performance findings."""
        critical_regressions = result.details.get("critical_regressions", 0)
        total_regressions = result.details.get("total_regressions", 0)
        
        if critical_regressions > 0:
            return ThreatLevel.CRITICAL
        elif total_regressions > 5:
            return ThreatLevel.HIGH
        elif total_regressions > 2:
            return ThreatLevel.MEDIUM
        elif total_regressions > 0:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.INFO
    
    def _calculate_reward(self, result: AgentResult) -> float:
        """Calculate RL reward for performance agent performance."""
        base_reward = super()._calculate_reward(result)
        
        # Additional reward for regression detection
        total_regressions = result.details.get("total_regressions", 0)
        if total_regressions > 0:
            base_reward += 0.2
        
        # Reward for critical regression detection
        critical_regressions = result.details.get("critical_regressions", 0)
        if critical_regressions > 0:
            base_reward += 0.3
        
        # Penalty for false positives (high regressions with low confidence)
        if total_regressions > 10 and result.confidence < 0.5:
            base_reward -= 0.2
        
        return max(-1.0, min(1.0, base_reward))
