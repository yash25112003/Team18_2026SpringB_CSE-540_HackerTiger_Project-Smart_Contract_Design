"""
Main orchestration system for the multi-agent validation team.
Coordinates all agents, manages sessions, and provides the primary interface.
"""

import asyncio
import logging
import sys
import argparse
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path

from utils.config import load_config
from utils.gemini_api import GeminiAPI
from utils.session import SessionManager
from utils.logging_utils import AuditLogger, StructuredLogger
from system_constitution import CONSTITUTION, VerdictType

# Import all agents
from agents import (
    SecurityAgent, RedTeamAgent, AnomalyAgent, ThreatModelAgent,
    ComplianceAgent, AuthorizationAgent, PerformanceAgent, ExplainabilityAgent,
    PrivacyAgent, DependencyAgent, EthicalAgent, EvoStrategist, VetoValidator
)


class MultiAgentValidator:
    """
    Main orchestration class for the multi-agent validation system.
    Coordinates all agents, manages sessions, and provides the primary interface.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the multi-agent validation system.
        
        Args:
            config_path: Optional path to configuration file
        """
        # Load configuration
        self.config = load_config(config_path)
        
        # Initialize core components
        self.gemini_api = GeminiAPI(
            api_keys=self.config.gemini_api_keys,
            model=self.config.gemini_model,
            temperature=self.config.gemini_temperature,
            demo_mode=self.config.demo_mode
        )
        
        self.session_manager = SessionManager(
            max_sessions=self.config.max_concurrent_agents,
            cleanup_interval=300
        )
        
        self.audit_logger = AuditLogger("audit.log")
        self.structured_logger = StructuredLogger("multi_agent_validator")
        
        # Initialize agents
        self.agents = {}
        self._initialize_agents()
        
        # Start background tasks
        asyncio.create_task(self.session_manager.start_cleanup_task())
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Multi-agent validation system initialized")
    
    def _initialize_agents(self):
        """Initialize all validation agents."""
        agent_classes = [
            SecurityAgent,
            RedTeamAgent,
            AnomalyAgent,
            ThreatModelAgent,
            ComplianceAgent,
            AuthorizationAgent,
            PerformanceAgent,
            ExplainabilityAgent,
            PrivacyAgent,
            DependencyAgent,
            EthicalAgent,
            EvoStrategist,
            VetoValidator
        ]
        
        for agent_class in agent_classes:
            if agent_class is not None:
                agent_name = agent_class.__name__.replace("Agent", "").replace("EvoStrategist", "Evo-Strategist")
                self.agents[agent_name] = agent_class

    def validate_payload_fields(self, payload: dict) -> list:
        required_fields = [
            "agent_id", "action", "timestamp", "version", "effective_date"
        ]
        missing = [field for field in required_fields if field not in payload]
        return missing
    
    async def validate_deployment(
        self,
        deployment_context: Dict[str, Any],
        agent_names: Optional[List[str]] = None,
        timeout_seconds: int = 300
    ) -> Dict[str, Any]:
        """
        Validate a deployment using the multi-agent system.
        
        Args:
            deployment_context: Context about the deployment to validate
            agent_names: Optional list of specific agents to use
            timeout_seconds: Session timeout in seconds
            
        Returns:
            Dict containing validation results and final verdict
        """
        try:
            # Validate payload
            missing_fields = self.validate_payload_fields(deployment_context)
            if missing_fields:
                print(f"⚠️ Warning: Deployment context missing required fields: {missing_fields}")
                # Optionally auto-fill defaults
                for field in missing_fields:
                    deployment_context[field] = f"default_{field}"  # You can customize default values
                print(f"✅ Auto-filled missing fields with defaults.")
            
            # Create validation session
            if agent_names is None:
                agent_names = list(self.agents.keys())
            
            session = await self.session_manager.create_session(
                deployment_context=deployment_context,
                agent_names=agent_names,
                timeout_seconds=timeout_seconds
            )
            
            self.logger.info(f"Created validation session {session.session_id}")
            
            # Execute agents in parallel
            agent_tasks = []
            error_counts = {"agent_failures": 0, "malformed_responses": 0, "guardrail_violations": 0}
            agent_guardrail_violations = {}
            
            for agent_name in agent_names:
                if agent_name in self.agents:
                    task = asyncio.create_task(
                        self._execute_agent(agent_name, session, deployment_context)
                    )
                    agent_tasks.append(task)
            
            # Wait for all agents to complete
            agent_results = await asyncio.gather(*agent_tasks, return_exceptions=True)
            
            # Process results
            successful_results = []
            failed_results = []
            
            for i, result in enumerate(agent_results):
                if isinstance(result, Exception):
                    failed_results.append({
                        "agent": agent_names[i],
                        "error": str(result)
                    })
                    error_counts["agent_failures"] += 1
                else:
                    successful_results.append(result)
                    # Count malformed responses
                    if hasattr(result, "error") and result.error:
                        if "Parse error" in str(result.error):
                            error_counts["malformed_responses"] += 1
                    # Count guardrail violations
                    details = getattr(result, "details", {})
                    guardrail = details.get("guardrail_validation", {})
                    violations = guardrail.get("violations_count", 0)
                    error_counts["guardrail_violations"] += violations
                    agent_guardrail_violations[result.agent_name] = violations
            
            # Execute consensus validation
            consensus_result = await self._execute_consensus_validation(
                session, successful_results, deployment_context
            )
            
            # Complete session
            await self.session_manager.complete_session(
                session.session_id, consensus_result.details
            )
            
            # Prepare enhanced final result with comprehensive audit trail
            final_result = {
                "session_id": session.session_id,
                "final_verdict": consensus_result.verdict if isinstance(consensus_result.verdict, str) else str(consensus_result.verdict),
                "consensus_score": consensus_result.details.get("consensus_score", 0.0),
                
                # Enhanced consensus and override information
                "quorum_threshold": consensus_result.details.get("quorum_threshold", 0.75),
                "override_triggered": consensus_result.details.get("override_triggered", False),
                "override_source": consensus_result.details.get("override_source"),
                "final_verdict_source": consensus_result.details.get("final_verdict_source", "quorum"),
                "threat_escalation": consensus_result.details.get("threat_escalation", False),
                "verdict_rationale": consensus_result.details.get("verdict_rationale", ""),
                "recommendations": consensus_result.details.get("recommendations", []),
                
                # Comprehensive agent results
                "agent_results": {
                    result.agent_name: result.to_dict() 
                    for result in successful_results
                },
                
                # Enhanced consensus analysis
                "consensus_analysis": consensus_result.details.get("consensus_analysis", {}),
                "system_metrics": consensus_result.details.get("system_metrics", {}),
                
                # Audit and compliance
                "audit_hash": consensus_result.details.get("audit_hash"),
                "ledger_block": consensus_result.details.get("ledger_block", {}),
                "failed_agents": failed_results,
                
                # Metadata
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "validation_version": "2.0.0",
                "compliance_standards": ["ISO27001", "SOC2", "NIST-CSF"]
            }
            
            # Add error summary to final result
            final_result["error_summary"] = error_counts
            final_result["agent_guardrail_violations"] = agent_guardrail_violations
            if error_counts["malformed_responses"] > 0:
                final_result["recommendations"].append(
                    f"Detected {error_counts['malformed_responses']} malformed agent responses. Review agent output formatting."
                )
            if error_counts["guardrail_violations"] > 0:
                final_result["recommendations"].append(
                    f"Detected {error_counts['guardrail_violations']} guardrail violations. Review payload completeness and agent logic."
                )
            
            # Handle threat escalation and notifications
            if final_result.get("threat_escalation", False):
                await self._handle_threat_escalation(final_result, session.session_id)
            
            self.logger.info(f"Validation completed for session {session.session_id}")
            return final_result
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return {
                "error": str(e),
                "session_id": session.session_id if 'session' in locals() else None,
                "final_verdict": "REJECT"
            }
    
    async def _execute_agent(
        self,
        agent_name: str,
        session,
        deployment_context: Dict[str, Any]
    ):
        """Execute a single agent."""
        try:
            agent_class = self.agents[agent_name]
            agent = agent_class(
                gemini_api=self.gemini_api,
                audit_logger=self.audit_logger,
                session=session
            )
            
            result = await agent.execute(deployment_context)
            
            # Update session with agent result
            await self.session_manager.update_session(
                session.session_id, agent_name, result.to_dict()
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Agent {agent_name} failed: {e}")
            await self.session_manager.mark_agent_failed(
                session.session_id, agent_name, str(e)
            )
            raise
    
    async def _execute_consensus_validation(self, session, agent_results: List, deployment_context: Dict[str, Any]):
        """Execute consensus validation using Veto-Validator."""
        try:
            # Check if VetoValidator is available
            if VetoValidator is None:
                self.logger.warning("VetoValidator not available, using simple consensus logic")
                return self._simple_consensus_validation(agent_results)
            
            # Create Veto-Validator agent
            veto_validator = VetoValidator(
                gemini_api=self.gemini_api,
                audit_logger=self.audit_logger,
                session=session
            )
            
            # Execute consensus validation
            consensus_result = await veto_validator.execute(deployment_context)
            
            return consensus_result
            
        except Exception as e:
            self.logger.error(f"Consensus validation failed: {e}")
            # Fallback to simple consensus
            return self._simple_consensus_validation(agent_results)
    
    def _simple_consensus_validation(self, agent_results: List):
        """Enhanced consensus validation with critical override logic."""
        from agents.base_agent import AgentResult, AgentStatus
        from system_constitution import VerdictType
        from datetime import datetime
        import hashlib
        import json
        
        if not agent_results:
            return AgentResult(
                agent_name="Consensus",
                session_id="",
                status=AgentStatus.FAILED,
                verdict=VerdictType.REJECT,
                confidence=0.0,
                details={"error": "No agent results available"},
                threat_level=5,
                execution_time=0.0,
                error="No agent results available"
            )
        
        # Critical override configuration
        CRITICAL_AGENTS = ["Red-Team-Specter", "Securo-Sentinel", "Threat-Model-Agent"]
        OVERRIDE_CONFIDENCE_THRESHOLD = 0.8
        QUORUM_THRESHOLD = 0.75
        
        # Initialize tracking variables
        verdict_counts = {}
        total_confidence = 0.0
        total_threat_level = 0.0
        override_triggered = False
        override_source = None
        final_verdict_source = "quorum"
        threat_escalation = False
        recommendations = []
        verdict_rationale = ""
        
        # Process agent results
        for result in agent_results:
            verdict = result.verdict
            verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
            total_confidence += result.confidence
            
            # Convert ThreatLevel enum to numeric value if needed
            threat_level_value = result.threat_level
            if threat_level_value is None:
                threat_level_value = 0.0
            elif hasattr(threat_level_value, 'value'):
                threat_level_value = threat_level_value.value
            total_threat_level += threat_level_value
            
            # Check for critical override conditions (handle both string and enum verdicts)
            verdict_str = verdict if isinstance(verdict, str) else verdict.value if hasattr(verdict, 'value') else str(verdict)
            if (result.agent_name in CRITICAL_AGENTS and 
                result.confidence >= OVERRIDE_CONFIDENCE_THRESHOLD and 
                verdict_str in ["REJECT", "ISOLATE"]):
                
                override_triggered = True
                override_source = result.agent_name
                final_verdict_source = "override"
                threat_escalation = True
                
                # Generate specific rationale for override
                if verdict_str == "ISOLATE":
                    verdict_rationale = f"CRITICAL OVERRIDE: {result.agent_name} triggered ISOLATE with {result.confidence:.2f} confidence due to severe security threat"
                    recommendations.append(f"Immediate isolation required - {result.agent_name} detected critical threat")
                else:
                    verdict_rationale = f"CRITICAL OVERRIDE: {result.agent_name} triggered REJECT with {result.confidence:.2f} confidence due to security concerns"
                    recommendations.append(f"Deployment rejected - {result.agent_name} identified security vulnerabilities")
                
                # Add agent-specific recommendations
                if hasattr(result, 'details') and result.details:
                    if 'recommendations' in result.details:
                        recommendations.extend(result.details['recommendations'][:3])  # Top 3 recommendations
                    if 'vulnerabilities' in result.details:
                        recommendations.append("Review and patch identified vulnerabilities immediately")
        
        # Determine final verdict
        if override_triggered:
            # Override takes precedence
            if verdict_counts.get("ISOLATE", 0) > 0:
                consensus_verdict = "ISOLATE"
            else:
                consensus_verdict = "REJECT"
        else:
            # Standard quorum logic
            if verdict_counts.get("ISOLATE", 0) > 0:
                consensus_verdict = "ISOLATE"
            elif verdict_counts.get("REJECT", 0) > verdict_counts.get("APPROVE", 0):
                consensus_verdict = "REJECT"
            else:
                consensus_verdict = "APPROVE"
                verdict_rationale = f"Quorum consensus: {verdict_counts.get('APPROVE', 0)} approve, {verdict_counts.get('REJECT', 0)} reject"
        
        # Calculate consensus score
        consensus_score = total_confidence / len(agent_results)
        avg_threat_level = total_threat_level / len(agent_results)
        
        # Generate additional recommendations if no override
        if not override_triggered:
            if consensus_verdict == "REJECT":
                recommendations.append("Review agent findings and address identified issues")
                recommendations.append("Consider additional security testing before redeployment")
            elif consensus_verdict == "APPROVE":
                recommendations.append("Proceed with deployment monitoring")
                recommendations.append("Continue regular security assessments")
        
        # Create comprehensive ledger block
        ledger_data = {
            "session_id": agent_results[0].session_id if agent_results else "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "verdict": consensus_verdict,
            "confidence": consensus_score,
            "quorum_threshold": QUORUM_THRESHOLD,
            "override_triggered": override_triggered,
            "override_source": override_source,
            "final_verdict_source": final_verdict_source,
            "threat_escalation": threat_escalation,
            "verdict_rationale": verdict_rationale,
            "recommendations": recommendations,
            "agent_results": [result.to_dict() for result in agent_results],
            "consensus_analysis": {
                "total_agents": len(agent_results),
                "average_confidence": consensus_score,
                "average_threat_level": avg_threat_level,
                "verdict_counts": verdict_counts
            },
            "system_metrics": {
                "total_execution_time": sum(result.execution_time for result in agent_results),
                "agent_count": len(agent_results),
                "critical_agents_participated": len([r for r in agent_results if r.agent_name in CRITICAL_AGENTS])
            }
        }
        
        # Generate audit hash for tamper-proof recordkeeping
        ledger_json = json.dumps(ledger_data, sort_keys=True, default=str)
        audit_hash = hashlib.sha256(ledger_json.encode('utf-8')).hexdigest()
        ledger_data["audit_hash"] = audit_hash
        
        return AgentResult(
            agent_name="Consensus",
            session_id=agent_results[0].session_id if agent_results else "",
            status=AgentStatus.COMPLETED,
            verdict=consensus_verdict,
            confidence=consensus_score,
            details=ledger_data,
            threat_level=avg_threat_level,
            execution_time=0.0,
            error=None
        )
    
    async def _handle_threat_escalation(self, final_result: Dict[str, Any], session_id: str):
        """Handle threat escalation and send notifications to security teams."""
        try:
            # Log critical security incident
            self.logger.critical(f"THREAT ESCALATION: Session {session_id} - {final_result.get('verdict_rationale', 'Unknown threat')}")
            
            # Create escalation record
            escalation_record = {
                "session_id": session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "severity": "CRITICAL",
                "override_source": final_result.get("override_source"),
                "verdict_rationale": final_result.get("verdict_rationale"),
                "recommendations": final_result.get("recommendations", []),
                "audit_hash": final_result.get("audit_hash"),
                "escalation_status": "ACTIVE"
            }
            
            # Log escalation for audit trail
            await self.audit_logger.log_action(
                agent_name="System",
                session_id=session_id,
                action="THREAT_ESCALATION",
                message=f"Critical security threat detected by {final_result.get('override_source')}",
                metadata=escalation_record
            )
            
            # In a real implementation, this would send notifications to:
            # - Security Operations Center (SOC)
            # - Incident Response Team
            # - Security Leadership
            # - Compliance Team
            
            self.logger.warning("SECURITY ALERT: Threat escalation triggered - manual intervention may be required")
            
        except Exception as e:
            self.logger.error(f"Failed to handle threat escalation: {e}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status and health information."""
        try:
            # Get session statistics
            session_stats = await self.session_manager.get_session_stats()
            
            # Get Gemini API health
            gemini_health = self.gemini_api.get_health_status()
            
            # Get agent health
            agent_health = {}
            for agent_name, agent_class in self.agents.items():
                agent_health[agent_name] = {
                    "status": "available",
                    "class": agent_class.__name__
                }
            
            return {
                "system_status": "operational",
                "session_stats": session_stats,
                "gemini_health": gemini_health,
                "agent_health": agent_health,
                "constitution_hash": CONSTITUTION.get_hash(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system status: {e}")
            return {
                "system_status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def shutdown(self):
        """Shutdown the multi-agent validation system."""
        try:
            # Shutdown session manager
            await self.session_manager.shutdown()
            
            # Shutdown audit logger
            self.audit_logger.shutdown()
            
            self.logger.info("Multi-agent validation system shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Shutdown error: {e}")


async def main():
    """Main entry point for the multi-agent validation system."""
    parser = argparse.ArgumentParser(description="Multi-Agent Validation System")
    parser.add_argument("--input", "-i", help="Input deployment JSON file")
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument("--agents", "-a", nargs="+", help="Specific agents to run")
    parser.add_argument("--timeout", "-t", type=int, default=300, help="Session timeout in seconds")
    parser.add_argument("--status", "-s", action="store_true", help="Show system status")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize validator
    validator = MultiAgentValidator(args.config)
    
    try:
        if args.status:
            # Show system status
            status = await validator.get_system_status()
            print("System Status:")
            print(json.dumps(status, indent=2))
            return
        
        if args.input:
            # Load deployment context from file
            with open(args.input, 'r') as f:
                deployment_context = json.load(f)
        else:
            # Use example deployment context
            deployment_context = {
            "commit_hash": "abc123def456",
            "author_metadata": {
                "name": "John Doe",
                "email": "john.doe@example.com"
            },
            "code": "def hello_world():\n    print('Hello, World!')",
            "dependencies": {
                "requests": "2.28.0",
                "numpy": "1.21.0"
            },
            "infrastructure": {
                "cloud_provider": "AWS",
                "region": "us-east-1"
            },
            "security_controls": {
                "encryption": True,
                "access_controls": True
            }
        }
        
        # Validate deployment
        result = await validator.validate_deployment(
            deployment_context=deployment_context,
            agent_names=args.agents,
            timeout_seconds=args.timeout
        )
        
        print("Validation Result:")
        print(json.dumps(result, indent=2))
        
        # Check for errors
        if "error" in result:
            print(f"\n❌ Validation failed: {result['error']}")
            sys.exit(1)
        else:
            print(f"\n✅ Validation completed successfully")
            print(f"Final Verdict: {result['final_verdict']}")
            print(f"Consensus Score: {result['consensus_score']:.2f}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    finally:
        # Shutdown system
        await validator.shutdown()


if __name__ == "__main__":
    asyncio.run(main())