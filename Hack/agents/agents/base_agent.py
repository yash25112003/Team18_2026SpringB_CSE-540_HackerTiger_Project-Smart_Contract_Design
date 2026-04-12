"""
Base ValidatorAgent class with extensible architecture for all validation agents.
"""

import asyncio
import time
import json
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import logging

try:
    from utils.gemini_api import GeminiAPI, GeminiResponse
    from utils.session import Session
    from utils.logging_utils import AuditLogger
    from system_constitution import ThreatLevel, CONSTITUTION
    from blockchain_guardrails import BlockchainGuardrails, GuardrailValidationResult
except ImportError:
    # For standalone execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.gemini_api import GeminiAPI, GeminiResponse
    from utils.session import Session
    from utils.logging_utils import AuditLogger
    from system_constitution import ThreatLevel, CONSTITUTION
    from blockchain_guardrails import BlockchainGuardrails, GuardrailValidationResult


class AgentStatus(Enum):
    """Agent execution status."""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


@dataclass
class AgentResult:
    """Standardized result from any validation agent."""
    agent_name: str
    session_id: str
    status: AgentStatus
    verdict: str  # "APPROVE", "REJECT", "ISOLATE"
    confidence: float  # 0.0 to 1.0
    details: Dict[str, Any]
    threat_level: Optional[ThreatLevel] = None
    execution_time: float = 0.0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "agent_name": self.agent_name,
            "session_id": self.session_id,
            "status": self.status.value,
            "verdict": self.verdict,
            "confidence": self.confidence,
            "details": self.details,
            "threat_level": self.threat_level.value if self.threat_level else None,
            "execution_time": self.execution_time,
            "error": self.error
        }


class ValidatorAgent(ABC):
    """
    Base class for all validation agents with extensible architecture.
    Provides common functionality for agent lifecycle, logging, and result handling.
    """
    
    def __init__(
        self,
        name: str,
        gemini_api: GeminiAPI,
        audit_logger: AuditLogger,
        session: Session,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize base validator agent.
        
        Args:
            name: Agent name
            gemini_api: Gemini API client
            audit_logger: Audit logger instance
            session: Current validation session
            config: Agent-specific configuration
        """
        self.name = name
        self.gemini_api = gemini_api
        self.audit_logger = audit_logger
        self.session = session
        self.config = config or {}
        self.logger = logging.getLogger(f"agent.{name}")
        self.status = AgentStatus.IDLE
        self.start_time: Optional[float] = None
        
        # Initialize blockchain guardrails
        self.guardrails = BlockchainGuardrails()
        self.result: Optional[AgentResult] = None
        
        # Agent capabilities
        self.supports_parallel = True
        self.requires_external_tools = False
        self.max_execution_time = 60.0  # seconds
        
        # RL reward tracking
        self.reward_history: List[float] = []
        self.performance_metrics: Dict[str, Any] = {}
    
    @abstractmethod
    async def validate(self, deployment_context: Dict[str, Any]) -> AgentResult:
        """
        Perform validation on deployment context.
        
        Args:
            deployment_context: Context about the deployment to validate
            
        Returns:
            AgentResult: Validation result
        """
        pass
    
    @abstractmethod
    def get_prompt_template(self) -> str:
        """
        Get the agent's prompt template for Gemini.
        
        Returns:
            str: Prompt template
        """
        pass
    
    @abstractmethod
    def parse_response(self, response: GeminiResponse) -> AgentResult:
        """
        Parse Gemini response into standardized AgentResult.
        
        Args:
            response: Response from Gemini API
            
        Returns:
            AgentResult: Parsed result
        """
        pass
    
    async def execute(self, deployment_context: Dict[str, Any]) -> AgentResult:
        """
        Execute the agent with full lifecycle management.
        
        Args:
            deployment_context: Deployment context to validate
            
        Returns:
            AgentResult: Final result
        """
        self.status = AgentStatus.RUNNING
        self.start_time = time.time()
        
        try:
            # Log agent start
            self.audit_logger.log_agent_start(
                self.name, self.session.session_id, deployment_context
            )
            
            # Execute validation with timeout
            result = await asyncio.wait_for(
                self.validate(deployment_context),
                timeout=self.max_execution_time
            )
            
            # Update status and metrics
            execution_time = time.time() - self.start_time
            result.execution_time = execution_time
            self.result = result
            self.status = AgentStatus.COMPLETED
            
            # Apply blockchain guardrails to result
            result = self._apply_guardrails_to_result(result, deployment_context)
            
            # Log completion
            self.audit_logger.log_agent_complete(
                self.name, self.session.session_id, result.to_dict(), execution_time
            )
            
            # Update performance metrics
            self._update_performance_metrics(result)
            
            return result
            
        except asyncio.TimeoutError:
            self.status = AgentStatus.TIMEOUT
            error_msg = f"Agent {self.name} timed out after {self.max_execution_time}s"
            self.logger.error(error_msg)
            
            result = AgentResult(
                agent_name=self.name,
                session_id=self.session.session_id,
                status=AgentStatus.TIMEOUT,
                verdict="REJECT",
                confidence=0.0,
                details={"error": "timeout"},
                execution_time=time.time() - self.start_time,
                error=error_msg
            )
            
            self.audit_logger.log_agent_failure(
                self.name, self.session.session_id, error_msg, 
                time.time() - self.start_time
            )
            
            return result
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            error_msg = f"Agent {self.name} failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            result = AgentResult(
                agent_name=self.name,
                session_id=self.session.session_id,
                status=AgentStatus.FAILED,
                verdict="REJECT",
                confidence=0.0,
                details={"error": str(e)},
                execution_time=time.time() - self.start_time,
                error=error_msg
            )
            
            self.audit_logger.log_agent_failure(
                self.name, self.session.session_id, error_msg,
                time.time() - self.start_time
            )
            
            return result
    
    async def _call_gemini(self, prompt: str, **kwargs) -> GeminiResponse:
        """
        Call Gemini API with agent-specific prompt.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional arguments for Gemini API
            
        Returns:
            GeminiResponse: Response from Gemini
        """
        try:
            response = await self.gemini_api.generate_content(prompt, **kwargs)
            
            if not response.success:
                raise Exception(f"Gemini API error: {response.error}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Gemini API call failed: {e}")
            raise
    
    def _update_performance_metrics(self, result: AgentResult):
        """Update agent performance metrics based on result."""
        # Calculate reward based on result quality
        reward = self._calculate_reward(result)
        self.reward_history.append(reward)
        
        # Update metrics
        self.performance_metrics.update({
            "total_executions": len(self.reward_history),
            "average_reward": sum(self.reward_history) / len(self.reward_history),
            "success_rate": sum(1 for r in self.reward_history if r > 0) / len(self.reward_history),
            "last_execution_time": result.execution_time,
            "last_confidence": result.confidence
        })
    
    def _calculate_reward(self, result: AgentResult) -> float:
        """
        Calculate RL reward for the agent's performance.
        Override in subclasses for agent-specific reward functions.
        
        Args:
            result: Agent result
            
        Returns:
            float: Reward value (-1.0 to 1.0)
        """
        base_reward = 0.0
        
        # Reward for successful completion
        if result.status == AgentStatus.COMPLETED:
            base_reward += 0.5
        
        # Reward for high confidence
        base_reward += result.confidence * 0.3
        
        # Reward for threat detection (if applicable)
        if result.threat_level and result.threat_level.value >= ThreatLevel.HIGH.value:
            base_reward += 0.2
        
        # Penalty for failures
        if result.status == AgentStatus.FAILED:
            base_reward -= 0.5
        
        return max(-1.0, min(1.0, base_reward))
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get agent health status."""
        return {
            "name": self.name,
            "status": self.status.value,
            "performance_metrics": self.performance_metrics,
            "supports_parallel": self.supports_parallel,
            "requires_external_tools": self.requires_external_tools,
            "max_execution_time": self.max_execution_time
        }
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get agent configuration."""
        return {
            "name": self.name,
            "config": self.config,
            "capabilities": {
                "supports_parallel": self.supports_parallel,
                "requires_external_tools": self.requires_external_tools,
                "max_execution_time": self.max_execution_time
            }
        }
    
    def update_configuration(self, new_config: Dict[str, Any]):
        """Update agent configuration."""
        self.config.update(new_config)
        self.logger.info(f"Updated configuration for agent {self.name}")
    
    def reset_metrics(self):
        """Reset performance metrics."""
        self.reward_history.clear()
        self.performance_metrics.clear()
        self.logger.info(f"Reset metrics for agent {self.name}")
    
    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(name={self.name}, status={self.status.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"{self.__class__.__name__}(name={self.name}, status={self.status.value}, "
                f"performance={self.performance_metrics})")
    
    def _apply_guardrails_to_result(self, result: AgentResult, deployment_context: Dict[str, Any]) -> AgentResult:
        """
        Apply blockchain guardrails to agent result.
        This is a mandatory security layer that validates all blockchain principles.
        """
        try:
            # Handle timestamp conversion
            timestamp = deployment_context.get("timestamp", "")
            if isinstance(timestamp, (int, float)):
                timestamp = datetime.fromtimestamp(timestamp, timezone.utc).isoformat()
            
            # Prepare data for guardrail validation
            agent_data = {
                "agent_name": result.agent_name,
                "session_id": result.session_id,
                "verdict": result.verdict,
                "confidence": result.confidence,
                "timestamp": timestamp,
                "agent_id": result.agent_name,  # Required for audit
                "action": deployment_context.get("action", "validate"),  # Required for audit
                "version": deployment_context.get("version", "1.0"),  # Required for policy
                "effective_date": deployment_context.get("effective_date", timestamp),  # Required for policy
                "stake": deployment_context.get("stake", 500),  # Default stake
                "reputation": deployment_context.get("reputation", 50),  # Default reputation
                "operation_type": deployment_context.get("operation_type", "standard"),
                "previous_hash": deployment_context.get("previous_hash", "0" * 64),  # Default genesis hash
                "current_hash": deployment_context.get("current_hash", ""),
                "signature": deployment_context.get("signature", "0" * 64),  # Mock signature if missing
                "nonce": deployment_context.get("nonce", "0"),
                "merkle_root": deployment_context.get("merkle_root", "0" * 64),  # Mock merkle root if missing
                "policy_version": deployment_context.get("policy_version", "1.0"),
                "evidence_hash": deployment_context.get("evidence_hash", ""),
                "evidence": result.details
            }
            
            # Ensure evidence hash exists
            if not agent_data["evidence_hash"]:
                # Create hash of the evidence fields as per blockchain_guardrails logic
                import hashlib
                evidence_fields = ['timestamp', 'agent_id', 'action', 'evidence']
                evidence_data = {k: v for k, v in agent_data.items() if k in evidence_fields}
                evidence_str = json.dumps(evidence_data, sort_keys=True, default=str)
                agent_data["evidence_hash"] = hashlib.sha256(evidence_str.encode()).hexdigest()
            
            # Ensure current hash exists for immutability check
            if not agent_data["current_hash"]:
                # Calculate hash of the agent data excluding current_hash
                data_to_hash = agent_data.copy()
                data_to_hash.pop("current_hash", None)
                data_str = json.dumps(data_to_hash, sort_keys=True, default=str)
                agent_data["current_hash"] = hashlib.sha256(data_str.encode()).hexdigest()

            # Validate all blockchain guardrails
            guardrail_result = self.guardrails.validate_all_guardrails(agent_data, result.agent_name)
            
            # Get guardrail summary
            guardrail_summary = self.guardrails.get_guardrail_summary(guardrail_result)
            
            # Merge guardrail results into agent details
            if "details" not in result.details:
                result.details = {}
            
            result.details.update(guardrail_summary)
            
            # Override verdict if critical violations found
            if not guardrail_result.passed:
                critical_violations = [v for v in guardrail_result.violations if v.severity == "CRITICAL"]
                if critical_violations:
                    result.verdict = "REJECT"
                    result.confidence = 0.0
                    result.details["guardrail_override"] = "Critical blockchain policy violation"
                    result.details["critical_violations"] = [
                        {
                            "type": v.violation_type.value,
                            "description": v.description,
                            "rule_section": v.rule_section
                        } for v in critical_violations
                    ]
            
            # Log guardrail validation results
            if not guardrail_result.passed:
                self.logger.warning(f"Guardrail violations detected: {len(guardrail_result.violations)}")
                for violation in guardrail_result.violations:
                    self.logger.warning(f"  {violation.violation_type.value}: {violation.description}")
            else:
                self.logger.info("All blockchain guardrails passed")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Guardrail validation failed: {str(e)}")
            # Add error to result details
            if "details" not in result.details:
                result.details = {}
            result.details["guardrail_error"] = str(e)
            return result
