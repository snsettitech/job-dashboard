# ai-service/app/services/cache_service.py
"""
Redis Caching Service for OpenAI Responses and Job Description Embeddings
Provides intelligent caching with TTL, compression, and cache invalidation strategies.
"""

import json
import hashlib
import pickle
import gzip
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import redis
from redis.exceptions import RedisError
import os

logger = logging.getLogger(__name__)

class CacheService:
    """Redis-based caching service for AI responses and embeddings"""
    
    def __init__(self):
        self.redis_client = None
        self._initialize_redis()
        
        # Cache configuration
        self.default_ttl = 3600  # 1 hour default
        self.embedding_ttl = 86400 * 7  # 7 days for embeddings
        self.openai_response_ttl = 3600 * 6  # 6 hours for OpenAI responses
        self.compression_threshold = 1024  # Compress data larger than 1KB
        
        # Cache key prefixes
        self.prefixes = {
            'embedding': 'emb',
            'openai_response': 'openai',
            'job_match': 'match',
            'optimization': 'opt',
            'session': 'sess',
            'health': 'health'
        }
    
    def _initialize_redis(self):
        """Initialize Redis connection with error handling"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6380")
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=False,  # Keep as bytes for compression
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
            
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing Redis: {e}")
            self.redis_client = None
    
    def _is_redis_available(self) -> bool:
        """Check if Redis is available"""
        if self.redis_client is None:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def _generate_cache_key(self, prefix: str, content: str, model: str = None) -> str:
        """Generate a unique cache key based on content hash and model"""
        # Create a hash of the content
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
        
        # Include model in key if provided
        if model:
            return f"{self.prefixes.get(prefix, prefix)}:{model}:{content_hash}"
        return f"{self.prefixes.get(prefix, prefix)}:{content_hash}"
    
    def _compress_data(self, data: bytes) -> bytes:
        """Compress data using gzip if it exceeds threshold"""
        if len(data) > self.compression_threshold:
            return gzip.compress(data)
        return data
    
    def _decompress_data(self, data: bytes) -> bytes:
        """Decompress data if it was compressed"""
        try:
            return gzip.decompress(data)
        except:
            return data
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data to bytes with compression"""
        serialized = pickle.dumps(data)
        return self._compress_data(serialized)
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserialize data from bytes with decompression"""
        try:
            decompressed = self._decompress_data(data)
            return pickle.loads(decompressed)
        except Exception as e:
            logger.error(f"Failed to deserialize cached data: {e}")
            return None
    
    async def cache_embedding(self, text: str, embedding: List[float], model: str = "text-embedding-3-small") -> bool:
        """Cache text embedding with model-specific key"""
        if not self._is_redis_available():
            return False
        
        try:
            cache_key = self._generate_cache_key('embedding', text, model)
            data = {
                'embedding': embedding,
                'model': model,
                'text_length': len(text),
                'cached_at': datetime.utcnow().isoformat()
            }
            
            serialized_data = self._serialize_data(data)
            self.redis_client.setex(
                cache_key,
                self.embedding_ttl,
                serialized_data
            )
            
            logger.debug(f"Cached embedding for text (length: {len(text)}) with key: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache embedding: {e}")
            return False
    
    async def get_cached_embedding(self, text: str, model: str = "text-embedding-3-small") -> Optional[List[float]]:
        """Retrieve cached embedding for text"""
        if not self._is_redis_available():
            return None
        
        try:
            cache_key = self._generate_cache_key('embedding', text, model)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = self._deserialize_data(cached_data)
                if data and 'embedding' in data:
                    logger.debug(f"Cache hit for embedding with key: {cache_key}")
                    return data['embedding']
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve cached embedding: {e}")
            return None
    
    async def cache_openai_response(self, prompt: str, response: str, model: str = "gpt-4o-mini", 
                                  temperature: float = 0.2, max_tokens: int = 1500) -> bool:
        """Cache OpenAI API response with prompt and parameters"""
        if not self._is_redis_available():
            return False
        
        try:
            # Create a unique key based on prompt and parameters
            prompt_hash = hashlib.sha256(
                f"{prompt}:{model}:{temperature}:{max_tokens}".encode('utf-8')
            ).hexdigest()[:16]
            
            cache_key = f"{self.prefixes['openai_response']}:{prompt_hash}"
            
            data = {
                'response': response,
                'model': model,
                'temperature': temperature,
                'max_tokens': max_tokens,
                'prompt_length': len(prompt),
                'cached_at': datetime.utcnow().isoformat()
            }
            
            serialized_data = self._serialize_data(data)
            self.redis_client.setex(
                cache_key,
                self.openai_response_ttl,
                serialized_data
            )
            
            logger.debug(f"Cached OpenAI response for prompt (length: {len(prompt)}) with key: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache OpenAI response: {e}")
            return False
    
    async def get_cached_openai_response(self, prompt: str, model: str = "gpt-4o-mini",
                                       temperature: float = 0.2, max_tokens: int = 1500) -> Optional[str]:
        """Retrieve cached OpenAI response"""
        if not self._is_redis_available():
            return None
        
        try:
            prompt_hash = hashlib.sha256(
                f"{prompt}:{model}:{temperature}:{max_tokens}".encode('utf-8')
            ).hexdigest()[:16]
            
            cache_key = f"{self.prefixes['openai_response']}:{prompt_hash}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = self._deserialize_data(cached_data)
                if data and 'response' in data:
                    logger.debug(f"Cache hit for OpenAI response with key: {cache_key}")
                    return data['response']
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve cached OpenAI response: {e}")
            return None
    
    async def cache_job_match_result(self, resume_text: str, job_description: str, 
                                   result: Dict[str, Any], user_id: Optional[str] = None) -> bool:
        """Cache job matching analysis result"""
        if not self._is_redis_available():
            return False
        
        try:
            # Create hash from resume and job description
            content_hash = hashlib.sha256(
                f"{resume_text}:{job_description}".encode('utf-8')
            ).hexdigest()[:16]
            
            cache_key = f"{self.prefixes['job_match']}:{content_hash}"
            if user_id:
                cache_key = f"{cache_key}:{user_id}"
            
            data = {
                'result': result,
                'resume_length': len(resume_text),
                'job_description_length': len(job_description),
                'user_id': user_id,
                'cached_at': datetime.utcnow().isoformat()
            }
            
            serialized_data = self._serialize_data(data)
            self.redis_client.setex(
                cache_key,
                self.default_ttl,
                serialized_data
            )
            
            logger.debug(f"Cached job match result with key: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache job match result: {e}")
            return False
    
    async def get_cached_job_match_result(self, resume_text: str, job_description: str,
                                        user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve cached job matching result"""
        if not self._is_redis_available():
            return None
        
        try:
            content_hash = hashlib.sha256(
                f"{resume_text}:{job_description}".encode('utf-8')
            ).hexdigest()[:16]
            
            cache_key = f"{self.prefixes['job_match']}:{content_hash}"
            if user_id:
                cache_key = f"{cache_key}:{user_id}"
            
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = self._deserialize_data(cached_data)
                if data and 'result' in data:
                    logger.debug(f"Cache hit for job match result with key: {cache_key}")
                    return data['result']
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve cached job match result: {e}")
            return None
    
    async def cache_optimization_result(self, resume_text: str, job_description: str,
                                      result: Dict[str, Any], user_id: Optional[str] = None) -> bool:
        """Cache resume optimization result"""
        if not self._is_redis_available():
            return False
        
        try:
            content_hash = hashlib.sha256(
                f"{resume_text}:{job_description}".encode('utf-8')
            ).hexdigest()[:16]
            
            cache_key = f"{self.prefixes['optimization']}:{content_hash}"
            if user_id:
                cache_key = f"{cache_key}:{user_id}"
            
            data = {
                'result': result,
                'resume_length': len(resume_text),
                'job_description_length': len(job_description),
                'user_id': user_id,
                'cached_at': datetime.utcnow().isoformat()
            }
            
            serialized_data = self._serialize_data(data)
            self.redis_client.setex(
                cache_key,
                self.default_ttl,
                serialized_data
            )
            
            logger.debug(f"Cached optimization result with key: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache optimization result: {e}")
            return False
    
    async def get_cached_optimization_result(self, resume_text: str, job_description: str,
                                           user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve cached optimization result"""
        if not self._is_redis_available():
            return None
        
        try:
            content_hash = hashlib.sha256(
                f"{resume_text}:{job_description}".encode('utf-8')
            ).hexdigest()[:16]
            
            cache_key = f"{self.prefixes['optimization']}:{content_hash}"
            if user_id:
                cache_key = f"{cache_key}:{user_id}"
            
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = self._deserialize_data(cached_data)
                if data and 'result' in data:
                    logger.debug(f"Cache hit for optimization result with key: {cache_key}")
                    return data['result']
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve cached optimization result: {e}")
            return None
    
    async def invalidate_user_cache(self, user_id: str) -> bool:
        """Invalidate all cache entries for a specific user"""
        if not self._is_redis_available():
            return False
        
        try:
            # Find all keys for this user
            pattern = f"*:{user_id}"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate user cache: {e}")
            return False
    
    async def clear_cache_by_prefix(self, prefix: str) -> bool:
        """Clear all cache entries with a specific prefix"""
        if not self._is_redis_available():
            return False
        
        try:
            pattern = f"{self.prefixes.get(prefix, prefix)}:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries with prefix {prefix}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear cache by prefix: {e}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics and health information"""
        if not self._is_redis_available():
            return {"status": "unavailable", "error": "Redis not connected"}
        
        try:
            info = self.redis_client.info()
            
            # Count keys by prefix
            key_counts = {}
            for prefix_name, prefix_value in self.prefixes.items():
                pattern = f"{prefix_value}:*"
                keys = self.redis_client.keys(pattern)
                key_counts[prefix_name] = len(keys)
            
            return {
                "status": "healthy",
                "redis_version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "key_counts": key_counts,
                "cache_ttl_settings": {
                    "default_ttl": self.default_ttl,
                    "embedding_ttl": self.embedding_ttl,
                    "openai_response_ttl": self.openai_response_ttl
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"status": "error", "error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Redis cache"""
        if not self._is_redis_available():
            return {
                "status": "unhealthy",
                "error": "Redis connection failed",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            # Test basic operations
            test_key = "health_check_test"
            test_value = "test_data"
            
            # Set and get test value
            self.redis_client.setex(test_key, 60, test_value)
            retrieved_value = self.redis_client.get(test_key)
            
            # Clean up test key
            self.redis_client.delete(test_key)
            
            if retrieved_value and retrieved_value.decode() == test_value:
                return {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "Redis cache is functioning correctly"
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Redis read/write test failed",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Global cache service instance
cache_service = CacheService()
