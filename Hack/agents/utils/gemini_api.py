"""
Gemini API utilities with key rotation and fallback mechanisms.
"""

import asyncio
import random
import time
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import logging


@dataclass
class GeminiResponse:
    """Structured response from Gemini API."""
    content: str
    success: bool
    error: Optional[str] = None
    usage_metadata: Optional[Dict[str, Any]] = None
    model_used: Optional[str] = None


class GeminiAPIError(Exception):
    """Custom exception for Gemini API errors."""
    pass


class GeminiAPI:
    """
    Advanced Gemini API client with key rotation, fallback, and retry mechanisms.
    """
    
    def __init__(self, api_keys: List[str], model: str = "gemini-1.5-pro", 
                 temperature: float = 0.1, demo_mode: bool = False):
        """
        Initialize Gemini API client.
        
        Args:
            api_keys: List of API keys for rotation
            model: Gemini model to use
            temperature: Temperature for generation
            demo_mode: Whether to run in demo mode (bypass API calls)
        """
        if not api_keys:
            raise ValueError("At least one API key must be provided")
        
        self.api_keys = api_keys
        self.model = model
        self.temperature = temperature
        self.demo_mode = demo_mode
        self.current_key_index = 0
        self.key_usage_stats = {key: {"success": 0, "failures": 0, "last_used": None} for key in api_keys}
        self.logger = logging.getLogger(__name__)
        
        # Initialize with first key
        if not self.demo_mode:
            self._configure_api()
    
    def _configure_api(self):
        """Configure the Gemini API with current key."""
        try:
            genai.configure(api_key=self.api_keys[self.current_key_index])
            self.logger.info(f"Configured Gemini API with key index {self.current_key_index}")
        except Exception as e:
            self.logger.error(f"Failed to configure Gemini API: {e}")
            raise GeminiAPIError(f"API configuration failed: {e}")
    
    def _rotate_key(self):
        """Rotate to next available API key."""
        original_index = self.current_key_index
        attempts = 0
        
        while attempts < len(self.api_keys):
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            attempts += 1
            
            try:
                self._configure_api()
                self.logger.info(f"Rotated to API key index {self.current_key_index}")
                return True
            except Exception as e:
                self.logger.warning(f"Failed to rotate to key {self.current_key_index}: {e}")
                continue
        
        # If all keys failed, reset to original
        self.current_key_index = original_index
        self._configure_api()
        return False
    
    def _update_key_stats(self, success: bool):
        """Update usage statistics for current key."""
        current_key = self.api_keys[self.current_key_index]
        stats = self.key_usage_stats[current_key]
        
        if success:
            stats["success"] += 1
        else:
            stats["failures"] += 1
        
        stats["last_used"] = time.time()
    
    def _get_best_key(self) -> str:
        """Get the best performing API key based on success rate."""
        best_key = None
        best_score = -1
        
        for key, stats in self.key_usage_stats.items():
            total_requests = stats["success"] + stats["failures"]
            if total_requests == 0:
                score = 1.0  # Prefer unused keys
            else:
                score = stats["success"] / total_requests
            
            if score > best_score:
                best_score = score
                best_key = key
        
        return best_key
    
    async def generate_content(
        self,
        prompt: str,
        max_retries: int = 3,
        timeout: int = 120,
        safety_settings: Optional[Dict[str, Any]] = None
    ) -> GeminiResponse:
        """
        Generate content using Gemini API with retry and fallback.
        
        Args:
            prompt: Input prompt
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
            safety_settings: Custom safety settings
            
        Returns:
            GeminiResponse: Structured response
        """
        if self.demo_mode:
            self.logger.info("DEMO MODE: Returning mock response")
            # Return a comprehensive mock JSON response that covers most agents
            mock_content = """
            {
                "analysis": "DEMO MODE: Simulated analysis of the provided context.",
                "verdict": "APPROVE",
                "pass_status": true,
                "confidence": 0.99,
                "risk_level": "LOW",
                "risk_score": 1.0,
                "issues": [],
                "recommendations": ["Proceed with deployment (Demo Mode)"],
                
                "vulnerabilities": [],
                "bug_bar_score": 0,
                "total_findings": 0,
                
                "attack_vectors": [],
                "successful_attacks": [],
                "mitigation_strategies": ["Standard mitigation"],
                
                "anomalies": [],
                "anomaly_score": 0.0,
                
                "compliance_status": "COMPLIANT",
                "violations": [],
                "compliance_summary": {
                    "overall_status": "COMPLIANT",
                    "critical_issues": 0,
                    "non_compliant_findings": 0
                },
                "compliance_report": {
                    "frameworks_checked": ["GDPR", "SOC2"],
                    "compliance_score": 100.0
                },
                
                "authorization_summary": {
                    "overall_status": "authorized",
                    "critical_issues": 0,
                    "security_violations": 0
                },
                "authorization_report": {
                    "authorization_score": 100.0
                },
                
                "performance_metrics": {
                    "latency": 10,
                    "throughput": 1000,
                    "resource_usage": "low"
                },
                "performance_summary": {
                    "performance_trend": "stable",
                    "regressions": [],
                    "overall_status": "PASS",
                    "critical_issues": 0
                },
                
                "privacy_score": 10.0,
                "data_leakage_risks": [],
                
                "ethical_score": 10.0,
                "bias_detected": false,
                "ethical_summary": {
                    "overall_status": "ETHICAL",
                    "overall_ethical_status": "COMPLIANT",
                    "critical_concerns": 0,
                    "legal_violations": 0
                },
                
                "explainability_score": 10.0,
                "explainability_summary": {
                    "overall_status": "EXPLAINABLE"
                },
                "executive_summary": {
                    "overall_status": "APPROVED",
                    "key_findings": ["Clear and explainable"],
                    "business_impact": "Positive"
                },
                
                "evolution_score": 10.0,
                "evolution_summary": {
                    "overall_status": "OPTIMAL"
                },
                "optimization_summary": {
                    "high_confidence_mutations": 5,
                    "expected_improvements": {"performance": "high"}
                },
                
                "dependencies": [],
                "vulnerable_dependencies": [],
                
                "final_verdict": "APPROVE",
                "consensus_analysis": {
                    "total_agents": 1,
                    "consensus_score": 1.0
                }
            }
            """
            return GeminiResponse(
                content=mock_content,
                success=True,
                model_used="demo-mock-model"
            )

        if not safety_settings:
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            }
        
        for attempt in range(max_retries):
            try:
                # Use asyncio to handle timeout
                response = await asyncio.wait_for(
                    self._make_request(prompt, safety_settings),
                    timeout=timeout
                )
                
                self._update_key_stats(True)
                return response
                
            except asyncio.TimeoutError:
                self.logger.warning(f"Request timeout on attempt {attempt + 1}")
                self._update_key_stats(False)
                
            except Exception as e:
                self.logger.warning(f"Request failed on attempt {attempt + 1}: {e}")
                self._update_key_stats(False)
                
                # Try rotating key on failure
                if attempt < max_retries - 1:
                    self._rotate_key()
            
            # Exponential backoff
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        
        # All attempts failed
        return GeminiResponse(
            content="",
            success=False,
            error="All API keys failed or timed out",
            model_used=self.model
        )
    
    async def _make_request(self, prompt: str, safety_settings: Dict[str, Any]) -> GeminiResponse:
        """Make actual request to Gemini API."""
        try:
            model = genai.GenerativeModel(
                model_name=self.model,
                safety_settings=safety_settings
            )
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.temperature,
                        max_output_tokens=8192,
                        top_p=0.8,
                        top_k=40
                    )
                )
            )
            
            if response.candidates and response.candidates[0].content:
                content = response.candidates[0].content.parts[0].text
                
                # Extract usage metadata if available
                usage_metadata = {}
                if hasattr(response, 'usage_metadata'):
                    usage_metadata = {
                        "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                        "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                        "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0)
                    }
                
                return GeminiResponse(
                    content=content,
                    success=True,
                    usage_metadata=usage_metadata,
                    model_used=self.model
                )
            else:
                return GeminiResponse(
                    content="",
                    success=False,
                    error="No content generated",
                    model_used=self.model
                )
                
        except Exception as e:
            raise GeminiAPIError(f"Gemini API request failed: {e}")
    
    async def batch_generate(
        self,
        prompts: List[str],
        max_concurrent: int = 5
    ) -> List[GeminiResponse]:
        """
        Generate content for multiple prompts concurrently.
        
        Args:
            prompts: List of prompts
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List of GeminiResponse objects
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_with_semaphore(prompt: str) -> GeminiResponse:
            async with semaphore:
                return await self.generate_content(prompt)
        
        tasks = [generate_with_semaphore(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_key_stats(self) -> Dict[str, Any]:
        """Get usage statistics for all API keys."""
        return {
            "current_key_index": self.current_key_index,
            "key_stats": self.key_usage_stats,
            "total_keys": len(self.api_keys)
        }
    
    def reset_key_stats(self):
        """Reset usage statistics for all keys."""
        for key in self.key_usage_stats:
            self.key_usage_stats[key] = {"success": 0, "failures": 0, "last_used": None}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the API client."""
        total_requests = sum(
            stats["success"] + stats["failures"] 
            for stats in self.key_usage_stats.values()
        )
        
        total_success = sum(
            stats["success"] for stats in self.key_usage_stats.values()
        )
        
        success_rate = total_success / total_requests if total_requests > 0 else 0
        
        return {
            "healthy": success_rate > 0.5,
            "success_rate": success_rate,
            "total_requests": total_requests,
            "available_keys": len(self.api_keys),
            "current_key": self.api_keys[self.current_key_index][:8] + "..."
        }
