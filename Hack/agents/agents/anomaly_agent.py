"""
"""

import json
import numpy as np
from dataclasses import dataclass
import asyncio
import time
from typing import Dict, Any, List, Optional
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

class AnomalyAgent(ValidatorAgent):
    """
    Sentinel-Orbit: ML/telemetry-based anomaly detection agent.
    Detects unknown and silent threats through behavioral analysis.
    """
    
    def __init__(self, gemini_api, audit_logger, session, config=None):
        super().__init__("Sentinel-Orbit", gemini_api, audit_logger, session, config)
        
        # Anomaly detection thresholds
        self.anomaly_thresholds = {
            "statistical": 3.0,  # Standard deviations
            "behavioral": 0.8,   # Similarity threshold
            "temporal": 0.7,     # Time-based threshold
            "pattern": 0.6       # Pattern matching threshold
        }
        
        # Baseline metrics for comparison
        self.baseline_metrics = {
            "cpu_usage": {"mean": 0.3, "std": 0.1, "max": 0.8},
            "memory_usage": {"mean": 0.4, "std": 0.15, "max": 0.9},
            "network_connections": {"mean": 50, "std": 20, "max": 200},
            "response_time": {"mean": 0.1, "std": 0.05, "max": 1.0},
            "error_rate": {"mean": 0.01, "std": 0.005, "max": 0.1}
        }
        
        # Anomaly patterns
        self.anomaly_patterns = {
            "sudden_spike": {"threshold": 5.0, "severity": 7},
            "gradual_drift": {"threshold": 2.0, "severity": 5},
            "periodic_anomaly": {"threshold": 3.0, "severity": 6},
            "outlier": {"threshold": 4.0, "severity": 8},
            "trend_change": {"threshold": 1.5, "severity": 4}
        }
    
    def get_prompt_template(self) -> str:
        """Get the anomaly detection prompt template."""
        return """
You are Sentinel-Orbit, an advanced anomaly detection agent specializing in ML/telemetry-based threat detection. Your mission is to analyze system behavior, telemetry data, and operational metrics to identify unknown and silent threats that may not be caught by traditional security tools.

## Analysis Context:
- Deployment Context: {deployment_context}
- Telemetry Data: {telemetry_data}
- Baseline Metrics: {baseline_metrics}
- Historical Data: {historical_data}

## Your Anomaly Detection Framework:

### 1. Behavioral Analysis
- **User Behavior**: Unusual access patterns, timing anomalies
- **System Behavior**: Unexpected resource usage, performance deviations
- **Network Behavior**: Unusual traffic patterns, connection anomalies
- **Application Behavior**: Unexpected API calls, data access patterns

### 2. Statistical Analysis
- **Outlier Detection**: Identify data points that deviate significantly
- **Trend Analysis**: Detect gradual changes in system behavior
- **Seasonal Analysis**: Identify unexpected seasonal patterns
- **Correlation Analysis**: Find unexpected relationships between metrics

### 3. Temporal Analysis
- **Time-based Anomalies**: Unusual timing patterns
- **Frequency Analysis**: Unexpected frequency of events
- **Duration Analysis**: Unusual duration of activities
- **Sequence Analysis**: Unexpected sequences of events

### 4. Pattern Recognition
- **Machine Learning Patterns**: Detect ML model behavior anomalies
- **Security Patterns**: Identify security-related anomalies
- **Operational Patterns**: Detect operational anomalies
- **Business Logic Patterns**: Identify business logic violations

### 5. Threat Indicators
Look for indicators of:
- **Insider Threats**: Unusual access patterns, data exfiltration
- **External Attacks**: Unusual network traffic, attack patterns
- **System Compromise**: Unexpected system behavior, resource usage
- **Data Breaches**: Unusual data access, large data transfers
- **Malware**: Unexpected processes, network connections
- **Advanced Persistent Threats**: Long-term behavioral changes

## Output Format:
Provide a comprehensive anomaly analysis in the following JSON structure:

```json
{{
    "anomalies_found": [
        {{
            "anomaly_type": "behavioral|statistical|temporal|pattern|network|resource|security",
            "severity": integer (1-10),
            "confidence": float (0.0-1.0),
            "description": "Detailed description of the anomaly",
            "indicators": ["indicator1", "indicator2"],
            "baseline": {{"metric": "value", "expected": "value"}},
            "deviation": {{"actual": "value", "expected": "value", "deviation": "percentage"}},
            "risk_factors": ["factor1", "factor2"],
            "recommendations": ["recommendation1", "recommendation2"]
        }}
    ],
    "severity": integer (1-10),
    "risk_score": float (0.0-10.0),
    "baseline_metrics": {{
        "normal_operations": {{"metric": "value"}},
        "expected_ranges": {{"metric": ["min", "max"]}}
    }},
    "recommendations": [
        "Priority recommendations based on anomaly findings"
    ],
    "threat_indicators": {{
        "insider_threat": boolean,
        "external_attack": boolean,
        "system_compromise": boolean,
        "data_breach": boolean,
        "malware": boolean,
        "apt": boolean
    }}
}}
```

## Anomaly Detection Guidelines:
1. **Be sensitive but specific** - Detect real anomalies, avoid false positives
2. **Consider context** - Anomalies may be normal in certain contexts
3. **Look for patterns** - Multiple small anomalies may indicate larger issues
4. **Consider timing** - Temporal patterns are often significant
5. **Assess impact** - Focus on anomalies with potential security impact
6. **Provide evidence** - Support findings with specific data points

Analyze the provided telemetry and behavioral data for anomalies and potential threats.
"""
    
    async def validate(self, deployment_context: Dict[str, Any]) -> AgentResult:
        """
        Perform comprehensive anomaly detection validation.
        
        Args:
            deployment_context: Deployment context to analyze
            
        Returns:
            AgentResult: Anomaly detection result
        """
        try:
            # Prepare analysis context
            analysis_context = self._prepare_analysis_context(deployment_context)
            
            # Generate anomaly detection prompt
            prompt = self.get_prompt_template().format(**analysis_context)
            
            # Call Gemini for analysis
            response = await self._call_gemini(prompt)
            
            # Parse and validate response
            result = self.parse_response(response)
            
            # Perform additional statistical analysis
            statistical_anomalies = await self._perform_statistical_analysis(deployment_context)
            
            # Merge results
            if statistical_anomalies:
                result.details["statistical_anomalies"] = statistical_anomalies
                result.details["total_anomalies"] = (
                    result.details.get("total_anomalies", 0) + len(statistical_anomalies)
                )
            
            # Determine threat level
            result.threat_level = self._determine_threat_level(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {e}")
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
        """Parse Gemini response into anomaly detection result."""
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
            anomalies_found = analysis_data.get("anomalies_found", [])
            severity = analysis_data.get("severity", 1)
            risk_score = analysis_data.get("risk_score", 0.0)
            
            # Determine verdict based on anomaly severity
            if severity >= 8:
                verdict = "ISOLATE"
            elif severity >= 6:
                verdict = "REJECT"
            elif severity >= 4:
                verdict = "REJECT"
            else:
                verdict = "APPROVE"
            
            # Calculate confidence
            confidence = self._calculate_confidence(analysis_data)
            
            # Prepare details
            details = {
                "anomalies_found": anomalies_found,
                "severity": severity,
                "risk_score": risk_score,
                "baseline_metrics": analysis_data.get("baseline_metrics", {}),
                "recommendations": analysis_data.get("recommendations", []),
                "threat_indicators": analysis_data.get("threat_indicators", {}),
                "total_anomalies": len(anomalies_found),
                "high_severity_anomalies": sum(1 for a in anomalies_found if a.get("severity", 0) >= 7)
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
            self.logger.error(f"Failed to parse anomaly response: {e}")
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
        """Prepare context for anomaly analysis."""
        # Generate synthetic telemetry data if not provided
        telemetry_data = deployment_context.get("telemetry_data", self._generate_synthetic_telemetry())
        
        return {
            "deployment_context": json.dumps(deployment_context, indent=2),
            "telemetry_data": json.dumps(telemetry_data, indent=2),
            "baseline_metrics": json.dumps(self.baseline_metrics, indent=2),
            "historical_data": json.dumps(deployment_context.get("historical_data", {}), indent=2)
        }
    
    def _generate_synthetic_telemetry(self) -> Dict[str, Any]:
        """Generate synthetic telemetry data for analysis."""
        import random
        
        # Generate normal telemetry with some anomalies
        telemetry = {
            "cpu_usage": [random.uniform(0.2, 0.6) for _ in range(100)],
            "memory_usage": [random.uniform(0.3, 0.7) for _ in range(100)],
            "network_connections": [random.randint(30, 80) for _ in range(100)],
            "response_time": [random.uniform(0.05, 0.2) for _ in range(100)],
            "error_rate": [random.uniform(0.005, 0.02) for _ in range(100)]
        }
        
        # Inject some anomalies
        if random.random() < 0.3:  # 30% chance of anomalies
            # CPU spike
            telemetry["cpu_usage"][50] = 0.95
            # Memory anomaly
            telemetry["memory_usage"][75] = 0.95
            # Network anomaly
            telemetry["network_connections"][25] = 500
        
        return telemetry
    
    async def _perform_statistical_analysis(self, deployment_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform statistical anomaly analysis."""
        anomalies = []
        
        # Get telemetry data
        telemetry_data = deployment_context.get("telemetry_data", self._generate_synthetic_telemetry())
        
        # Analyze each metric
        for metric_name, values in telemetry_data.items():
            if isinstance(values, list) and len(values) > 10:
                baseline = self.baseline_metrics.get(metric_name, {"mean": 0.5, "std": 0.1})
                
                # Calculate statistics
                mean_val = np.mean(values)
                std_val = np.std(values)
                baseline_mean = baseline["mean"]
                baseline_std = baseline["std"]
                
                # Detect outliers
                z_scores = [(x - baseline_mean) / baseline_std for x in values]
                outliers = [i for i, z in enumerate(z_scores) if abs(z) > 3.0]
                
                if outliers:
                    anomalies.append({
                        "metric": metric_name,
                        "anomaly_type": "statistical",
                        "severity": min(10, len(outliers) + 5),
                        "confidence": 0.8,
                        "description": f"Statistical anomaly in {metric_name}: {len(outliers)} outliers detected",
                        "indicators": [f"Z-score > 3.0 at positions {outliers[:5]}"],
                        "baseline": {"mean": baseline_mean, "std": baseline_std},
                        "deviation": {"actual_mean": mean_val, "expected_mean": baseline_mean},
                        "risk_factors": ["Statistical deviation", "Potential system issue"],
                        "recommendations": [f"Investigate {metric_name} anomalies", "Review system performance"]
                    })
        
        return anomalies
    
    def _calculate_confidence(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the anomaly analysis."""
        base_confidence = 0.7
        
        # Increase confidence based on anomaly diversity
        anomalies_found = analysis_data.get("anomalies_found", [])
        if anomalies_found:
            anomaly_types = set(anomaly.get("anomaly_type", "") for anomaly in anomalies_found)
            if len(anomaly_types) > 2:
                base_confidence += 0.1
        
        # Increase confidence for detailed threat indicators
        threat_indicators = analysis_data.get("threat_indicators", {})
        if threat_indicators and any(threat_indicators.values()):
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _determine_threat_level(self, result: AgentResult) -> ThreatLevel:
        """Determine threat level based on anomaly findings."""
        severity = result.details.get("severity", 1)
        high_severity_anomalies = result.details.get("high_severity_anomalies", 0)
        
        if severity >= 8 or high_severity_anomalies >= 3:
            return ThreatLevel.CRITICAL
        elif severity >= 6 or high_severity_anomalies >= 2:
            return ThreatLevel.HIGH
        elif severity >= 4 or high_severity_anomalies >= 1:
            return ThreatLevel.MEDIUM
        elif severity >= 2:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.INFO
    
    def _calculate_reward(self, result: AgentResult) -> float:
        """Calculate RL reward for anomaly detection performance."""
        base_reward = super()._calculate_reward(result)
        
        # Additional reward for anomaly detection
        total_anomalies = result.details.get("total_anomalies", 0)
        if total_anomalies > 0:
            base_reward += 0.2
        
        # Reward for high-severity anomaly detection
        high_severity_anomalies = result.details.get("high_severity_anomalies", 0)
        if high_severity_anomalies > 0:
            base_reward += 0.3
        
        # Penalty for false positives (high anomaly count with low confidence)
        if total_anomalies > 10 and result.confidence < 0.5:
            base_reward -= 0.2
        
        return max(-1.0, min(1.0, base_reward))
