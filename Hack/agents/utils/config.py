"""
Configuration management for the multi-agent validation system.
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class Config:
    """Configuration class for the multi-agent validation system."""
    
    # Gemini API Configuration
    gemini_api_keys: List[str]
    gemini_model: str = "gemini-1.5-pro"
    gemini_temperature: float = 0.1
    
    # System Configuration
    consensus_quorum_threshold: float = 0.75
    max_concurrent_agents: int = 12
    session_timeout_seconds: int = 300
    audit_log_retention_days: int = 365
    
    # Security Configuration
    enable_red_team_testing: bool = True
    enable_adversarial_analysis: bool = True
    threat_modeling_enabled: bool = True
    anomaly_detection_sensitivity: float = 0.8
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"
    enable_structured_logging: bool = True
    
    # Blockchain Configuration
    blockchain_network: str = "mainnet"
    immutable_logging: bool = True
    hash_algorithm: str = "SHA256"

    # Demo Mode
    demo_mode: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.gemini_api_keys:
            raise ValueError("At least one Gemini API key must be provided")
        
        if not 0.0 <= self.consensus_quorum_threshold <= 1.0:
            raise ValueError("Consensus quorum threshold must be between 0.0 and 1.0")
        
        if self.max_concurrent_agents < 1:
            raise ValueError("Max concurrent agents must be at least 1")
        
        if self.session_timeout_seconds < 60:
            raise ValueError("Session timeout must be at least 60 seconds")


def load_config(env_file: Optional[str] = None) -> Config:
    """
    Load configuration from environment variables and optional .env file.
    
    Args:
        env_file: Optional path to .env file
        
    Returns:
        Config: Loaded configuration object
    """
    # Load environment variables
    if env_file and os.path.exists(env_file):
        load_dotenv(env_file)
    else:
        load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    # Parse Gemini API keys
    api_keys_str = os.getenv("GEMINI_API_KEYS", "")
    if not api_keys_str and os.getenv("GEMINI_API_KEY"):
        api_keys_str = os.getenv("GEMINI_API_KEY", "")
    if not api_keys_str:
        raise ValueError("GEMINI_API_KEYS or GEMINI_API_KEY environment variable is required")
    
    api_keys = [key.strip() for key in api_keys_str.split(",") if key.strip()]
    
    # Parse boolean values
    def parse_bool(value: str, default: bool = False) -> bool:
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")
    
    # Parse float values
    def parse_float(value: str, default: float) -> float:
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            return default
    
    # Parse int values
    def parse_int(value: str, default: int) -> int:
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    
    return Config(
        gemini_api_keys=api_keys,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-pro"),
        gemini_temperature=parse_float(os.getenv("GEMINI_TEMPERATURE", "0.1"), 0.1),
        
        consensus_quorum_threshold=parse_float(
            os.getenv("CONSENSUS_QUORUM_THRESHOLD", "0.75"), 0.75
        ),
        max_concurrent_agents=parse_int(
            os.getenv("MAX_CONCURRENT_AGENTS", "12"), 12
        ),
        session_timeout_seconds=parse_int(
            os.getenv("SESSION_TIMEOUT_SECONDS", "300"), 300
        ),
        audit_log_retention_days=parse_int(
            os.getenv("AUDIT_LOG_RETENTION_DAYS", "365"), 365
        ),
        
        enable_red_team_testing=parse_bool(
            os.getenv("ENABLE_RED_TEAM_TESTING", "true"), True
        ),
        enable_adversarial_analysis=parse_bool(
            os.getenv("ENABLE_ADVERSARIAL_ANALYSIS", "true"), True
        ),
        threat_modeling_enabled=parse_bool(
            os.getenv("THREAT_MODELING_ENABLED", "true"), True
        ),
        anomaly_detection_sensitivity=parse_float(
            os.getenv("ANOMALY_DETECTION_SENSITIVITY", "0.8"), 0.8
        ),
        
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_format=os.getenv("LOG_FORMAT", "json"),
        enable_structured_logging=parse_bool(
            os.getenv("ENABLE_STRUCTURED_LOGGING", "true"), True
        ),
        
        blockchain_network=os.getenv("BLOCKCHAIN_NETWORK", "mainnet"),
        immutable_logging=parse_bool(
            os.getenv("IMMUTABLE_LOGGING", "true"), True
        ),
        hash_algorithm=os.getenv("HASH_ALGORITHM", "SHA256"),
        
        demo_mode=parse_bool(os.getenv("DEMO_MODE", "false"), False)
    )


# Global config instance - lazy loading
_config = None

def get_config() -> Config:
    """Get the global config instance, loading it if necessary."""
    global _config
    if _config is None:
        _config = load_config()
    return _config

# For backward compatibility
config = get_config()
