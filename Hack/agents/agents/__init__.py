"""
Multi-agent validation system agents.
"""

import asyncio
from .base_agent import ValidatorAgent, AgentResult, AgentStatus
from .security_agent import SecurityAgent
from .red_team_agent import RedTeamAgent

# Import other agents with error handling
try:
    from .anomaly_agent import AnomalyAgent
except ImportError:
    AnomalyAgent = None

try:
    from .threat_model_agent import ThreatModelAgent
except ImportError:
    ThreatModelAgent = None

try:
    from .compliance_agent import ComplianceAgent
except ImportError:
    ComplianceAgent = None

try:
    from .authorization_agent import AuthorizationAgent
except ImportError:
    AuthorizationAgent = None

try:
    from .performance_agent import PerformanceAgent
except ImportError:
    PerformanceAgent = None

try:
    from .explainability_agent import ExplainabilityAgent
except ImportError:
    ExplainabilityAgent = None

try:
    from .privacy_agent import PrivacyAgent
except ImportError:
    PrivacyAgent = None

try:
    from .dependency_agent import DependencyAgent
except ImportError:
    DependencyAgent = None

try:
    from .ethical_agent import EthicalAgent
except ImportError:
    EthicalAgent = None

try:
    from .evo_strategist import EvoStrategist
except ImportError:
    EvoStrategist = None

try:
    from .veto_validator import VetoValidator
except ImportError:
    VetoValidator = None

__all__ = [
    'ValidatorAgent', 'AgentResult', 'AgentStatus',
    'SecurityAgent', 'RedTeamAgent', 'AnomalyAgent', 'ThreatModelAgent',
    'ComplianceAgent', 'AuthorizationAgent', 'PerformanceAgent',
    'ExplainabilityAgent', 'PrivacyAgent', 'DependencyAgent',
    'EthicalAgent', 'EvoStrategist', 'VetoValidator'
]
