# backend/app/services/ai_health_checker.py
"""
AI Service Health Checker Module

Provides comprehensive health checking for AI services to ensure
reliability and prevent fallback to mock data when AI is unavailable.
"""

import openai
import os
import time
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of AI service health check"""
    status: HealthStatus
    response_time_ms: float
    error_message: Optional[str] = None
    details: Dict = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.details is None:
            self.details = {}


class AIServiceHealthChecker:
    """Comprehensive health checking for AI services"""

    def __init__(self):
        self.client = None  # Initialize lazily
        self.last_health_check: Optional[HealthCheckResult] = None
        self.health_check_cache_duration = 60  # Cache health status for 60 seconds

        # Health thresholds
        self.max_response_time_ms = 10000  # 10 seconds
        self.min_response_quality_threshold = 0.7

    def _get_client(self):
        """Lazy initialization of OpenAI client"""
        if self.client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise Exception("OpenAI API key not configured")
            self.client = openai.OpenAI(api_key=api_key)
        return self.client
    
    async def check_ai_service_health(self, force_check: bool = False) -> HealthCheckResult:
        """
        Comprehensive health check of AI services
        Returns cached result if recent check available (unless force_check=True)
        """
        # Return cached result if available and recent
        if (not force_check and 
            self.last_health_check and 
            time.time() - self.last_health_check.timestamp < self.health_check_cache_duration):
            return self.last_health_check
        
        start_time = time.time()
        
        try:
            # Test 1: Basic connectivity and API key validation
            connectivity_result = await self._test_basic_connectivity()
            if connectivity_result.status != HealthStatus.HEALTHY:
                return self._cache_and_return(connectivity_result)
            
            # Test 2: Embedding service functionality
            embedding_result = await self._test_embedding_service()
            if embedding_result.status != HealthStatus.HEALTHY:
                return self._cache_and_return(embedding_result)
            
            # Test 3: Chat completion service functionality
            chat_result = await self._test_chat_completion_service()
            if chat_result.status != HealthStatus.HEALTHY:
                return self._cache_and_return(chat_result)
            
            # Test 4: Response quality validation
            quality_result = await self._test_response_quality()
            if quality_result.status != HealthStatus.HEALTHY:
                return self._cache_and_return(quality_result)
            
            # All tests passed
            total_time = (time.time() - start_time) * 1000
            
            result = HealthCheckResult(
                status=HealthStatus.HEALTHY,
                response_time_ms=total_time,
                details={
                    "connectivity_check": "PASSED",
                    "embedding_service": "PASSED",
                    "chat_completion_service": "PASSED",
                    "response_quality": "PASSED",
                    "api_key_valid": True,
                    "all_services_operational": True
                }
            )
            
            return self._cache_and_return(result)
            
        except Exception as e:
            total_time = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                response_time_ms=total_time,
                error_message=f"Health check failed: {str(e)}",
                details={
                    "error_type": "HEALTH_CHECK_EXCEPTION",
                    "error_details": str(e)
                }
            )
            return self._cache_and_return(result)
    
    async def _test_basic_connectivity(self) -> HealthCheckResult:
        """Test basic OpenAI API connectivity"""
        try:
            start_time = time.time()
            client = self._get_client()

            # Simple API call to test connectivity
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5,
                temperature=0
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response_time > self.max_response_time_ms:
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED,
                    response_time_ms=response_time,
                    error_message=f"API response time too slow: {response_time:.0f}ms",
                    details={"test": "connectivity", "threshold_ms": self.max_response_time_ms}
                )
            
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                details={"test": "connectivity", "api_responsive": True}
            )
            
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                error_message=f"Connectivity test failed: {str(e)}",
                details={"test": "connectivity", "error": str(e)}
            )
    
    async def _test_embedding_service(self) -> HealthCheckResult:
        """Test embedding service functionality"""
        try:
            start_time = time.time()
            client = self._get_client()

            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=["test embedding functionality"]
            )
            
            response_time = (time.time() - start_time) * 1000
            
            # Validate response
            if not response.data or len(response.data) == 0:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    error_message="Embedding service returned empty response",
                    details={"test": "embeddings", "response_empty": True}
                )
            
            embedding = response.data[0].embedding
            if not embedding or len(embedding) == 0:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    error_message="Embedding service returned invalid embedding",
                    details={"test": "embeddings", "embedding_invalid": True}
                )
            
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                details={
                    "test": "embeddings",
                    "embedding_dimensions": len(embedding),
                    "service_functional": True
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                error_message=f"Embedding service test failed: {str(e)}",
                details={"test": "embeddings", "error": str(e)}
            )
    
    async def _test_chat_completion_service(self) -> HealthCheckResult:
        """Test chat completion service functionality"""
        try:
            start_time = time.time()
            client = self._get_client()

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Respond with exactly 'TEST_PASSED'."},
                    {"role": "user", "content": "Please respond with the test phrase."}
                ],
                max_tokens=10,
                temperature=0
            )
            
            response_time = (time.time() - start_time) * 1000
            
            # Validate response
            if not response.choices or len(response.choices) == 0:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    error_message="Chat completion service returned empty response",
                    details={"test": "chat_completion", "response_empty": True}
                )
            
            content = response.choices[0].message.content.strip()
            if "TEST_PASSED" not in content:
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED,
                    response_time_ms=response_time,
                    error_message="Chat completion service response quality degraded",
                    details={
                        "test": "chat_completion",
                        "expected": "TEST_PASSED",
                        "received": content,
                        "quality_degraded": True
                    }
                )
            
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                details={
                    "test": "chat_completion",
                    "response_correct": True,
                    "service_functional": True
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                error_message=f"Chat completion service test failed: {str(e)}",
                details={"test": "chat_completion", "error": str(e)}
            )
    
    async def _test_response_quality(self) -> HealthCheckResult:
        """Test AI response quality for resume optimization tasks"""
        try:
            start_time = time.time()
            client = self._get_client()

            test_prompt = """
Analyze this resume snippet and provide improvement suggestions:
"Software Engineer with experience in Python and web development."

Return your analysis as JSON with this structure:
{
    "improvements": ["suggestion1", "suggestion2"],
    "quality_score": 0.8
}
"""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert resume analyst. Always return valid JSON."},
                    {"role": "user", "content": test_prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            response_time = (time.time() - start_time) * 1000
            
            # Validate JSON response
            try:
                content = response.choices[0].message.content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                
                parsed_response = json.loads(content)
                
                # Check for required fields
                if "improvements" not in parsed_response or "quality_score" not in parsed_response:
                    return HealthCheckResult(
                        status=HealthStatus.DEGRADED,
                        response_time_ms=response_time,
                        error_message="AI response missing required fields",
                        details={
                            "test": "response_quality",
                            "missing_fields": True,
                            "response": content[:200]
                        }
                    )
                
                quality_score = parsed_response.get("quality_score", 0)
                if quality_score < self.min_response_quality_threshold:
                    return HealthCheckResult(
                        status=HealthStatus.DEGRADED,
                        response_time_ms=response_time,
                        error_message=f"AI response quality below threshold: {quality_score}",
                        details={
                            "test": "response_quality",
                            "quality_score": quality_score,
                            "threshold": self.min_response_quality_threshold
                        }
                    )
                
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    details={
                        "test": "response_quality",
                        "quality_score": quality_score,
                        "json_valid": True,
                        "fields_present": True
                    }
                )
                
            except json.JSONDecodeError as e:
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED,
                    response_time_ms=response_time,
                    error_message="AI returned invalid JSON",
                    details={
                        "test": "response_quality",
                        "json_error": str(e),
                        "response": content[:200]
                    }
                )
            
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                error_message=f"Response quality test failed: {str(e)}",
                details={"test": "response_quality", "error": str(e)}
            )
    
    def _cache_and_return(self, result: HealthCheckResult) -> HealthCheckResult:
        """Cache the health check result and return it"""
        self.last_health_check = result
        logger.info(f"AI service health check completed: {result.status.value} in {result.response_time_ms:.0f}ms")
        return result
    
    def is_service_healthy(self) -> bool:
        """Quick check if service is healthy based on last health check"""
        if not self.last_health_check:
            return False
        
        # Check if cached result is still valid
        if time.time() - self.last_health_check.timestamp > self.health_check_cache_duration:
            return False
        
        return self.last_health_check.status == HealthStatus.HEALTHY
    
    def get_health_summary(self) -> Dict:
        """Get a summary of current health status"""
        if not self.last_health_check:
            return {
                "status": "unknown",
                "message": "No health check performed yet",
                "last_check": None
            }
        
        return {
            "status": self.last_health_check.status.value,
            "response_time_ms": self.last_health_check.response_time_ms,
            "last_check": self.last_health_check.timestamp,
            "error_message": self.last_health_check.error_message,
            "details": self.last_health_check.details
        }


# Global health checker instance
ai_health_checker = AIServiceHealthChecker()
