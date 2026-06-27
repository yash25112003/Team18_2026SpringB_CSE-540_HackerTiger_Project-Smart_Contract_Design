"""
Advanced logging utilities for the multi-agent validation system.
"""

import json
import logging
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
from queue import Queue
import time
import asyncio


@dataclass(frozen=True)
class LogEntry:
    """Structured log entry with immutability."""
    timestamp: str
    level: str
    agent_name: str
    session_id: str
    action: str
    message: str
    metadata: Dict[str, Any]
    hash: str
    
    def __post_init__(self):
        """Generate hash for immutable logging."""
        if not self.hash:
            object.__setattr__(self, 'hash', self._generate_hash())
    
    def _generate_hash(self) -> str:
        """Generate SHA256 hash of the log entry."""
        entry_data = {
            "timestamp": self.timestamp,
            "level": self.level,
            "agent_name": self.agent_name,
            "session_id": self.session_id,
            "action": self.action,
            "message": self.message,
            "metadata": self.metadata
        }
        entry_json = json.dumps(entry_data, sort_keys=True)
        return hashlib.sha256(entry_json.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class StructuredLogger:
    """Structured logger with immutable audit capabilities."""
    
    def __init__(self, name: str, log_file: Optional[str] = None, 
                 enable_console: bool = True, log_level: str = "INFO"):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
            log_file: Optional log file path
            enable_console: Enable console output
            log_level: Logging level
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(file_handler)
        
        # Thread-safe queue for batch processing
        self.log_queue = Queue()
        self.batch_size = 100
        self.flush_interval = 5.0
        self._shutdown = False
        
        # Start background thread for batch processing
        self._batch_thread = threading.Thread(target=self._batch_processor, daemon=True)
        self._batch_thread.start()
    
    def _batch_processor(self):
        """Background thread for batch log processing."""
        batch = []
        last_flush = time.time()
        
        while not self._shutdown:
            try:
                # Get log entry with timeout
                entry = self.log_queue.get(timeout=1.0)
                batch.append(entry)
                
                # Flush if batch is full or time interval passed
                current_time = time.time()
                if (len(batch) >= self.batch_size or 
                    current_time - last_flush >= self.flush_interval):
                    self._flush_batch(batch)
                    batch = []
                    last_flush = current_time
                    
            except:
                # Timeout or shutdown
                if batch:
                    self._flush_batch(batch)
                    batch = []
                continue
    
    def _flush_batch(self, batch: List[LogEntry]):
        """Flush a batch of log entries."""
        for entry in batch:
            self._write_entry(entry)
    
    def _write_entry(self, entry: LogEntry):
        """Write a single log entry."""
        log_message = json.dumps(entry.to_dict())
        
        if entry.level.upper() == "ERROR":
            self.logger.error(log_message)
        elif entry.level.upper() == "WARNING":
            self.logger.warning(log_message)
        elif entry.level.upper() == "INFO":
            self.logger.info(log_message)
        else:
            self.logger.debug(log_message)
    
    def log(self, level: str, agent_name: str, session_id: str, 
             action: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Log a structured entry."""
        entry = LogEntry(
            timestamp=datetime.utcnow().isoformat(),
            level=level.upper(),
            agent_name=agent_name,
            session_id=session_id,
            action=action,
            message=message,
            metadata=metadata or {},
            hash=""  # Will be generated in __post_init__
        )
        
        self.log_queue.put(entry)
    
    def info(self, agent_name: str, session_id: str, action: str, 
             message: str, metadata: Optional[Dict[str, Any]] = None):
        """Log info level message."""
        self.log("INFO", agent_name, session_id, action, message, metadata)
    
    def warning(self, agent_name: str, session_id: str, action: str, 
                message: str, metadata: Optional[Dict[str, Any]] = None):
        """Log warning level message."""
        self.log("WARNING", agent_name, session_id, action, message, metadata)
    
    def error(self, agent_name: str, session_id: str, action: str, 
              message: str, metadata: Optional[Dict[str, Any]] = None):
        """Log error level message."""
        self.log("ERROR", agent_name, session_id, action, message, metadata)
    
    def debug(self, agent_name: str, session_id: str, action: str, 
              message: str, metadata: Optional[Dict[str, Any]] = None):
        """Log debug level message."""
        self.log("DEBUG", agent_name, session_id, action, message, metadata)
    
    def flush(self):
        """Force flush of pending log entries."""
        batch = []
        while not self.log_queue.empty():
            try:
                entry = self.log_queue.get_nowait()
                batch.append(entry)
            except:
                break
        
        if batch:
            self._flush_batch(batch)
    
    def shutdown(self):
        """Shutdown logger and flush remaining entries."""
        self._shutdown = True
        self._batch_thread.join(timeout=5.0)
        
        # Flush remaining entries
        while not self.log_queue.empty():
            try:
                entry = self.log_queue.get_nowait()
                self._write_entry(entry)
            except:
                break


class AuditLogger:
    """Specialized audit logger for immutable audit trails."""
    
    def __init__(self, audit_file: str, enable_verification: bool = True):
        """
        Initialize audit logger.
        
        Args:
            audit_file: Path to audit log file
            enable_verification: Enable hash verification
        """
        self.audit_file = Path(audit_file)
        self.enable_verification = enable_verification
        self.logger = StructuredLogger("audit", str(self.audit_file))
        
        # Create audit file if it doesn't exist
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.audit_file.exists():
            self.audit_file.touch()
    
    def log_agent_start(self, agent_name: str, session_id: str, 
                        deployment_context: Dict[str, Any]):
        """Log agent start event."""
        self.logger.info(
            agent_name, session_id, "AGENT_START",
            f"Agent {agent_name} started validation",
            {"deployment_context": deployment_context}
        )
    
    def log_agent_complete(self, agent_name: str, session_id: str, 
                           result: Dict[str, Any], duration: float):
        """Log agent completion event."""
        self.logger.info(
            agent_name, session_id, "AGENT_COMPLETE",
            f"Agent {agent_name} completed validation in {duration:.2f}s",
            {"result": result, "duration_seconds": duration}
        )
    
    def log_agent_failure(self, agent_name: str, session_id: str, 
                          error: str, duration: float):
        """Log agent failure event."""
        self.logger.error(
            agent_name, session_id, "AGENT_FAILURE",
            f"Agent {agent_name} failed: {error}",
            {"error": error, "duration_seconds": duration}
        )
    
    def log_consensus_start(self, session_id: str, agent_count: int):
        """Log consensus process start."""
        self.logger.info(
            "CONSENSUS", session_id, "CONSENSUS_START",
            f"Starting consensus process with {agent_count} agents",
            {"agent_count": agent_count}
        )
    
    def log_consensus_complete(self, session_id: str, verdict: str, 
                              consensus_score: float, duration: float):
        """Log consensus completion."""
        self.logger.info(
            "CONSENSUS", session_id, "CONSENSUS_COMPLETE",
            f"Consensus completed: {verdict} (score: {consensus_score:.2f})",
            {"verdict": verdict, "consensus_score": consensus_score, "duration_seconds": duration}
        )
    
    def log_threat_detected(self, agent_name: str, session_id: str, 
                           threat_type: str, severity: int, details: Dict[str, Any]):
        """Log threat detection."""
        self.logger.warning(
            agent_name, session_id, "THREAT_DETECTED",
            f"Threat detected: {threat_type} (severity: {severity})",
            {"threat_type": threat_type, "severity": severity, "details": details}
        )
    
    def log_system_event(self, event_type: str, session_id: str, 
                        message: str, metadata: Optional[Dict[str, Any]] = None):
        """Log system-level event."""
        self.logger.info(
            "SYSTEM", session_id, event_type, message, metadata or {}
        )
    
    def verify_audit_integrity(self) -> Dict[str, Any]:
        """Verify integrity of audit log."""
        if not self.enable_verification:
            return {"verified": True, "message": "Verification disabled"}
        
        try:
            with open(self.audit_file, 'r') as f:
                lines = f.readlines()
            
            verified_entries = 0
            failed_entries = 0
            
            for line in lines:
                if line.strip():
                    try:
                        # Extract JSON from log line (format: timestamp - logger - level - JSON)
                        # Find the last " - " and extract JSON from there
                        json_start = line.rfind(' - {')
                        if json_start != -1:
                            json_str = line[json_start + 3:].strip()  # Skip " - " prefix
                        else:
                            # Try to parse the entire line as JSON (fallback)
                            json_str = line.strip()
                        
                        entry_data = json.loads(json_str)
                        entry = LogEntry(**entry_data)
                        
                        # Verify hash
                        expected_hash = entry._generate_hash()
                        if entry.hash == expected_hash:
                            verified_entries += 1
                        else:
                            failed_entries += 1
                    except Exception:
                        failed_entries += 1
            
            return {
                "verified": failed_entries == 0,
                "total_entries": len(lines),
                "verified_entries": verified_entries,
                "failed_entries": failed_entries,
                "integrity_score": verified_entries / len(lines) if lines else 1.0
            }
            
        except Exception as e:
            return {
                "verified": False,
                "error": str(e),
                "message": "Failed to verify audit integrity"
            }
    
    def get_audit_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get audit summary for a session or all sessions."""
        try:
            with open(self.audit_file, 'r') as f:
                lines = f.readlines()
            
            entries = []
            for line in lines:
                if line.strip():
                    try:
                        # Extract JSON from log line (format: timestamp - logger - level - JSON)
                        json_start = line.rfind(' - {')
                        if json_start != -1:
                            json_str = line[json_start + 3:].strip()  # Skip " - " prefix
                        else:
                            # Try to parse the entire line as JSON (fallback)
                            json_str = line.strip()
                        
                        entry_data = json.loads(json_str)
                        if session_id is None or entry_data.get("session_id") == session_id:
                            entries.append(entry_data)
                    except Exception:
                        continue
            
            # Analyze entries
            agent_activities = {}
            threat_detections = []
            consensus_events = []
            
            for entry in entries:
                agent_name = entry.get("agent_name", "UNKNOWN")
                action = entry.get("action", "UNKNOWN")
                
                if agent_name not in agent_activities:
                    agent_activities[agent_name] = {"start": 0, "complete": 0, "failure": 0}
                
                if action == "AGENT_START":
                    agent_activities[agent_name]["start"] += 1
                elif action == "AGENT_COMPLETE":
                    agent_activities[agent_name]["complete"] += 1
                elif action == "AGENT_FAILURE":
                    agent_activities[agent_name]["failure"] += 1
                elif action == "THREAT_DETECTED":
                    threat_detections.append(entry)
                elif action in ["CONSENSUS_START", "CONSENSUS_COMPLETE"]:
                    consensus_events.append(entry)
            
            return {
                "total_entries": len(entries),
                "agent_activities": agent_activities,
                "threat_detections": len(threat_detections),
                "consensus_events": len(consensus_events),
                "session_id": session_id,
                "time_range": {
                    "start": entries[0]["timestamp"] if entries else None,
                    "end": entries[-1]["timestamp"] if entries else None
                }
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "message": "Failed to generate audit summary"
            }
    
    def flush(self):
        """Force flush of pending log entries."""
        self.logger.flush()
    
    def shutdown(self):
        """Shutdown audit logger."""
        self.logger.shutdown()
