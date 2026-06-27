"""
Session management for multi-agent validation system.
"""

import uuid
import time
import asyncio
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging


class SessionStatus(Enum):
    """Session status enumeration."""
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"


@dataclass
class Session:
    """Session data structure for tracking validation sessions."""
    
    session_id: str
    created_at: datetime
    status: SessionStatus = SessionStatus.ACTIVE
    deployment_context: Dict[str, Any] = field(default_factory=dict)
    agent_results: Dict[str, Any] = field(default_factory=dict)
    consensus_result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 300
    
    def __post_init__(self):
        """Initialize session after creation."""
        self.last_activity = datetime.utcnow()
        self.agent_participants: Set[str] = set()
        self.completed_agents: Set[str] = set()
        self.failed_agents: Set[str] = set()
    
    def is_expired(self) -> bool:
        """Check if session has expired."""
        if self.status in [SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.CANCELLED]:
            return True
        
        return datetime.utcnow() - self.last_activity > timedelta(seconds=self.timeout_seconds)
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def add_agent_result(self, agent_name: str, result: Dict[str, Any]):
        """Add result from an agent."""
        self.agent_results[agent_name] = result
        self.completed_agents.add(agent_name)
        self.update_activity()
    
    def mark_agent_failed(self, agent_name: str, error: str):
        """Mark an agent as failed."""
        self.agent_results[agent_name] = {"error": error, "success": False}
        self.failed_agents.add(agent_name)
        self.update_activity()
    
    def get_completion_rate(self) -> float:
        """Get completion rate of agents."""
        if not self.agent_participants:
            return 0.0
        return len(self.completed_agents) / len(self.agent_participants)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "deployment_context": self.deployment_context,
            "agent_results": self.agent_results,
            "consensus_result": self.consensus_result,
            "metadata": self.metadata,
            "timeout_seconds": self.timeout_seconds,
            "last_activity": self.last_activity.isoformat(),
            "agent_participants": list(self.agent_participants),
            "completed_agents": list(self.completed_agents),
            "failed_agents": list(self.failed_agents),
            "completion_rate": self.get_completion_rate()
        }


class SessionManager:
    """Manages validation sessions and agent coordination."""
    
    def __init__(self, max_sessions: int = 100, cleanup_interval: int = 300):
        """
        Initialize session manager.
        
        Args:
            max_sessions: Maximum number of concurrent sessions
            cleanup_interval: Cleanup interval in seconds
        """
        self.sessions: Dict[str, Session] = {}
        self.max_sessions = max_sessions
        self.cleanup_interval = cleanup_interval
        self.logger = logging.getLogger(__name__)
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start_cleanup_task(self):
        """Start background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_expired_sessions()
            except Exception as e:
                self.logger.error(f"Cleanup task error: {e}")
    
    async def create_session(
        self,
        deployment_context: Dict[str, Any],
        agent_names: List[str],
        timeout_seconds: int = 300,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """
        Create a new validation session.
        
        Args:
            deployment_context: Context about the deployment
            agent_names: List of agent names that will participate
            timeout_seconds: Session timeout
            metadata: Optional metadata
            
        Returns:
            Session: Created session
        """
        if len(self.sessions) >= self.max_sessions:
            # Remove oldest session
            oldest_session = min(
                self.sessions.values(),
                key=lambda s: s.created_at
            )
            await self.remove_session(oldest_session.session_id)
        
        session_id = str(uuid.uuid4())
        session = Session(
            session_id=session_id,
            created_at=datetime.utcnow(),
            deployment_context=deployment_context,
            timeout_seconds=timeout_seconds,
            metadata=metadata or {}
        )
        
        # Set agent participants after creation
        session.agent_participants = set(agent_names)
        
        self.sessions[session_id] = session
        self.logger.info(f"Created session {session_id} with {len(agent_names)} agents")
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        return self.sessions.get(session_id)
    
    async def update_session(
        self,
        session_id: str,
        agent_name: str,
        result: Dict[str, Any]
    ) -> bool:
        """
        Update session with agent result.
        
        Args:
            session_id: Session ID
            agent_name: Agent name
            result: Agent result
            
        Returns:
            bool: Success status
        """
        session = await self.get_session(session_id)
        if not session:
            return False
        
        if session.is_expired():
            session.status = SessionStatus.TIMEOUT
            return False
        
        session.add_agent_result(agent_name, result)
        return True
    
    async def mark_agent_failed(
        self,
        session_id: str,
        agent_name: str,
        error: str
    ) -> bool:
        """Mark an agent as failed in the session."""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.mark_agent_failed(agent_name, error)
        return True
    
    async def complete_session(
        self,
        session_id: str,
        consensus_result: Dict[str, Any]
    ) -> bool:
        """Mark session as completed with consensus result."""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.consensus_result = consensus_result
        session.status = SessionStatus.COMPLETED
        session.update_activity()
        
        self.logger.info(f"Completed session {session_id}")
        return True
    
    async def fail_session(self, session_id: str, reason: str) -> bool:
        """Mark session as failed."""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.status = SessionStatus.FAILED
        session.metadata["failure_reason"] = reason
        session.update_activity()
        
        self.logger.warning(f"Failed session {session_id}: {reason}")
        return True
    
    async def cancel_session(self, session_id: str, reason: str) -> bool:
        """Cancel a session."""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.status = SessionStatus.CANCELLED
        session.metadata["cancellation_reason"] = reason
        session.update_activity()
        
        self.logger.info(f"Cancelled session {session_id}: {reason}")
        return True
    
    async def remove_session(self, session_id: str) -> bool:
        """Remove session from manager."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.logger.info(f"Removed session {session_id}")
            return True
        return False
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if session.is_expired()
        ]
        
        for session_id in expired_sessions:
            session = self.sessions[session_id]
            if session.status == SessionStatus.ACTIVE:
                session.status = SessionStatus.TIMEOUT
            await self.remove_session(session_id)
        
        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        total_sessions = len(self.sessions)
        active_sessions = sum(1 for s in self.sessions.values() if s.status == SessionStatus.ACTIVE)
        completed_sessions = sum(1 for s in self.sessions.values() if s.status == SessionStatus.COMPLETED)
        failed_sessions = sum(1 for s in self.sessions.values() if s.status == SessionStatus.FAILED)
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "completed_sessions": completed_sessions,
            "failed_sessions": failed_sessions,
            "max_sessions": self.max_sessions,
            "cleanup_interval": self.cleanup_interval
        }
    
    async def get_active_sessions(self) -> List[Session]:
        """Get all active sessions."""
        return [
            session for session in self.sessions.values()
            if session.status == SessionStatus.ACTIVE
        ]
    
    async def shutdown(self):
        """Shutdown session manager and cleanup."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Mark all active sessions as cancelled
        for session in self.sessions.values():
            if session.status == SessionStatus.ACTIVE:
                session.status = SessionStatus.CANCELLED
                session.metadata["shutdown_reason"] = "System shutdown"
        
        self.logger.info("Session manager shutdown complete")
