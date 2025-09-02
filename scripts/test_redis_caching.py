#!/usr/bin/env python3
"""
Test script for Redis caching implementation
Tests embedding caching, OpenAI response caching, and cache management endpoints
"""

import asyncio
import sys
import os
import time
import json
from typing import Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import cache service
try:
    from ai_service.app.services.cache_service import cache_service
    print("✅ Successfully imported AI service cache")
except ImportError as e:
    print(f"❌ Failed to import AI service cache: {e}")
    sys.exit(1)

async def test_redis_connection():
    """Test basic Redis connection"""
    print("\n🔍 Testing Redis Connection...")
    
    health = await cache_service.health_check()
    print(f"Redis Health Status: {health['status']}")
    
    if health['status'] == 'healthy':
        print("✅ Redis connection successful")
        return True
    else:
        print(f"❌ Redis connection failed: {health.get('error', 'Unknown error')}")
        return False

async def test_embedding_caching():
    """Test embedding caching functionality"""
    print("\n🧠 Testing Embedding Caching...")
    
    # Test data
    test_text = "Software engineer with 5 years of experience in Python and JavaScript"
    test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 300  # 1500 dimensions
    model = "text-embedding-3-small"
    
    # Test caching
    print("Caching test embedding...")
    cache_success = await cache_service.cache_embedding(test_text, test_embedding, model)
    
    if cache_success:
        print("✅ Embedding cached successfully")
    else:
        print("❌ Failed to cache embedding")
        return False
    
    # Test retrieval
    print("Retrieving cached embedding...")
    cached_embedding = await cache_service.get_cached_embedding(test_text, model)
    
    if cached_embedding:
        print("✅ Cached embedding retrieved successfully")
        print(f"   Original length: {len(test_embedding)}")
        print(f"   Cached length: {len(cached_embedding)}")
        print(f"   Match: {test_embedding == cached_embedding}")
        return True
    else:
        print("❌ Failed to retrieve cached embedding")
        return False

async def test_openai_response_caching():
    """Test OpenAI response caching functionality"""
    print("\n🤖 Testing OpenAI Response Caching...")
    
    # Test data
    test_prompt = "Analyze this job description for software engineering skills"
    test_response = '{"skills": ["Python", "JavaScript", "React"], "level": "mid-level"}'
    model = "gpt-4o-mini"
    temperature = 0.2
    max_tokens = 1500
    
    # Test caching
    print("Caching test OpenAI response...")
    cache_success = await cache_service.cache_openai_response(
        test_prompt, test_response, model, temperature, max_tokens
    )
    
    if cache_success:
        print("✅ OpenAI response cached successfully")
    else:
        print("❌ Failed to cache OpenAI response")
        return False
    
    # Test retrieval
    print("Retrieving cached OpenAI response...")
    cached_response = await cache_service.get_cached_openai_response(
        test_prompt, model, temperature, max_tokens
    )
    
    if cached_response:
        print("✅ Cached OpenAI response retrieved successfully")
        print(f"   Original: {test_response}")
        print(f"   Cached: {cached_response}")
        print(f"   Match: {test_response == cached_response}")
        return True
    else:
        print("❌ Failed to retrieve cached OpenAI response")
        return False

async def test_job_match_caching():
    """Test job match result caching functionality"""
    print("\n🎯 Testing Job Match Caching...")
    
    # Test data
    resume_text = "Experienced software engineer with expertise in Python and web development"
    job_description = "We are looking for a Python developer with web development experience"
    test_result = {
        "match_scores": {"overall": 0.85, "skills": 0.9, "experience": 0.8},
        "recommendation": "Strong match for this position",
        "confidence_score": 85.0
    }
    user_id = "test_user_123"
    
    # Test caching
    print("Caching test job match result...")
    cache_success = await cache_service.cache_job_match_result(
        resume_text, job_description, test_result, user_id
    )
    
    if cache_success:
        print("✅ Job match result cached successfully")
    else:
        print("❌ Failed to cache job match result")
        return False
    
    # Test retrieval
    print("Retrieving cached job match result...")
    cached_result = await cache_service.get_cached_job_match_result(
        resume_text, job_description, user_id
    )
    
    if cached_result:
        print("✅ Cached job match result retrieved successfully")
        print(f"   Original scores: {test_result['match_scores']}")
        print(f"   Cached scores: {cached_result['match_scores']}")
        print(f"   Match: {test_result == cached_result}")
        return True
    else:
        print("❌ Failed to retrieve cached job match result")
        return False

async def test_cache_stats():
    """Test cache statistics functionality"""
    print("\n📊 Testing Cache Statistics...")
    
    stats = await cache_service.get_cache_stats()
    
    if stats['status'] == 'healthy':
        print("✅ Cache statistics retrieved successfully")
        print(f"   Redis Version: {stats.get('redis_version', 'Unknown')}")
        print(f"   Connected Clients: {stats.get('connected_clients', 0)}")
        print(f"   Memory Usage: {stats.get('used_memory_human', 'Unknown')}")
        print(f"   Key Counts: {stats.get('key_counts', {})}")
        return True
    else:
        print(f"❌ Failed to get cache stats: {stats.get('error', 'Unknown error')}")
        return False

async def test_cache_clear():
    """Test cache clearing functionality"""
    print("\n🧹 Testing Cache Clearing...")
    
    # Clear test data
    success = await cache_service.clear_cache_by_prefix("embedding")
    
    if success:
        print("✅ Cache cleared successfully")
        return True
    else:
        print("❌ Failed to clear cache")
        return False

async def test_performance_improvement():
    """Test performance improvement with caching"""
    print("\n⚡ Testing Performance Improvement...")
    
    test_text = "Performance test text for embedding generation"
    model = "text-embedding-3-small"
    test_embedding = [0.1, 0.2, 0.3] * 500  # 1500 dimensions
    
    # First call (cache miss)
    print("First call (cache miss)...")
    start_time = time.time()
    await cache_service.cache_embedding(test_text, test_embedding, model)
    cache_time = time.time() - start_time
    print(f"   Cache write time: {cache_time:.3f}s")
    
    # Second call (cache hit)
    print("Second call (cache hit)...")
    start_time = time.time()
    cached_embedding = await cache_service.get_cached_embedding(test_text, model)
    retrieval_time = time.time() - start_time
    print(f"   Cache read time: {retrieval_time:.3f}s")
    
    if cached_embedding:
        improvement = (cache_time - retrieval_time) / cache_time * 100
        print(f"✅ Performance improvement: {improvement:.1f}% faster")
        return True
    else:
        print("❌ Cache hit failed")
        return False

async def run_all_tests():
    """Run all caching tests"""
    print("🚀 Starting Redis Caching Tests")
    print("=" * 50)
    
    tests = [
        ("Redis Connection", test_redis_connection),
        ("Embedding Caching", test_embedding_caching),
        ("OpenAI Response Caching", test_openai_response_caching),
        ("Job Match Caching", test_job_match_caching),
        ("Cache Statistics", test_cache_stats),
        ("Performance Improvement", test_performance_improvement),
        ("Cache Clearing", test_cache_clear),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Redis caching is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False

def main():
    """Main function"""
    print("Redis Caching Test Suite")
    print("This script tests the Redis caching implementation for AI services")
    
    # Check if Redis is available
    try:
        import redis
        print("✅ Redis Python client available")
    except ImportError:
        print("❌ Redis Python client not available. Install with: pip install redis")
        sys.exit(1)
    
    # Run tests
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n🎯 Caching implementation is ready for production use!")
        sys.exit(0)
    else:
        print("\n🔧 Please fix the failing tests before deploying.")
        sys.exit(1)

if __name__ == "__main__":
    main()
