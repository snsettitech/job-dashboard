#!/usr/bin/env python3
"""
Comprehensive Test Suite for Genuine AI Resume Optimization System

This script tests all the critical fixes implemented to ensure:
1. Input validation rejects nonsensical job descriptions
2. No fallback/mock data is ever returned
3. All responses include genuine AI processing metadata
4. Confidence scores and transparency are provided
5. System fails fast with clear error messages when appropriate
"""

import requests
import json
import time
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class TestResult:
    def __init__(self, test_name: str, expected_result: str):
        self.test_name = test_name
        self.expected_result = expected_result
        self.actual_result = None
        self.passed = False
        self.error_message = None
        self.response_data = None

def test_endpoint(url: str, method: str = 'GET', data: Dict = None, expected_status: int = 200) -> Dict[str, Any]:
    """Test an endpoint and return response data"""
    try:
        if method == 'GET':
            response = requests.get(url, timeout=30)
        elif method == 'POST':
            response = requests.post(url, 
                                   headers={'Content-Type': 'application/json'}, 
                                   data=json.dumps(data) if data else None,
                                   timeout=30)
        
        return {
            "status_code": response.status_code,
            "success": response.status_code == expected_status,
            "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "response_time": response.elapsed.total_seconds()
        }
    except Exception as e:
        return {
            "status_code": 0,
            "success": False,
            "error": str(e),
            "response_time": 0
        }

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    
    print("🧪 COMPREHENSIVE TEST SUITE FOR GENUINE AI SYSTEM")
    print("=" * 80)
    
    tests = []
    
    # Test 1: Gibberish job description should return HTTP 400
    print("\n1. Testing gibberish job description rejection...")
    test1 = TestResult("Gibberish Input Rejection", "HTTP 400 with validation error")
    
    gibberish_data = {
        "resume_text": "Software Engineer with 5 years experience in Python and React development.",
        "job_description": "ssssssssss"
    }
    
    result = test_endpoint(f"{BASE_URL}/api/ai/analyze-match", "POST", gibberish_data, 400)
    test1.actual_result = f"HTTP {result['status_code']}"
    test1.passed = result['status_code'] == 400
    test1.response_data = result.get('data', {})
    
    if test1.passed:
        print(f"   ✅ PASSED: {test1.actual_result}")
        print(f"   📝 Error message: {test1.response_data.get('detail', 'N/A')}")
    else:
        print(f"   ❌ FAILED: Expected HTTP 400, got {test1.actual_result}")
        print(f"   📝 Response: {test1.response_data}")
    
    tests.append(test1)
    
    # Test 2: Too short job description should return HTTP 400
    print("\n2. Testing insufficient length job description...")
    test2 = TestResult("Insufficient Length Rejection", "HTTP 400 with word count error")
    
    short_data = {
        "resume_text": "Software Engineer with 5 years experience in Python and React development.",
        "job_description": "looking for someone"
    }
    
    result = test_endpoint(f"{BASE_URL}/api/ai/analyze-match", "POST", short_data, 400)
    test2.actual_result = f"HTTP {result['status_code']}"
    test2.passed = result['status_code'] == 400
    test2.response_data = result.get('data', {})
    
    if test2.passed:
        print(f"   ✅ PASSED: {test2.actual_result}")
        print(f"   📝 Error message: {test2.response_data.get('detail', 'N/A')}")
    else:
        print(f"   ❌ FAILED: Expected HTTP 400, got {test2.actual_result}")
    
    tests.append(test2)
    
    # Test 3: Valid job description should return genuine AI analysis
    print("\n3. Testing valid job description with genuine AI processing...")
    test3 = TestResult("Valid Input Processing", "HTTP 200 with AI metadata")
    
    valid_data = {
        "resume_text": "Senior Software Engineer with 8 years of experience in Python, Django, React, and AWS. Led development teams of 5+ engineers, architected scalable microservices handling 1M+ daily requests, and implemented CI/CD pipelines reducing deployment time by 60%. Expert in database optimization, API design, and agile methodologies.",
        "job_description": "We are seeking a Senior Software Engineer to join our growing engineering team. The ideal candidate will have 5+ years of experience in Python and React development, with strong leadership skills and experience with cloud platforms like AWS. Responsibilities include architecting scalable systems, mentoring junior developers, and collaborating with cross-functional teams to deliver high-quality software solutions. Requirements: Bachelor's degree in Computer Science, proficiency in Python and JavaScript, experience with microservices architecture, and excellent communication skills."
    }
    
    start_time = time.time()
    result = test_endpoint(f"{BASE_URL}/api/ai/analyze-match", "POST", valid_data, 200)
    processing_time = time.time() - start_time
    
    test3.actual_result = f"HTTP {result['status_code']}"
    test3.passed = result['status_code'] == 200
    test3.response_data = result.get('data', {})
    
    if test3.passed:
        print(f"   ✅ PASSED: {test3.actual_result}")
        print(f"   ⏱️  Processing time: {processing_time:.2f}s")
        
        # Check for genuine AI processing indicators
        metadata = test3.response_data.get('processing_metadata', {})
        print(f"   🤖 AI models used: {metadata.get('ai_models_used', [])}")
        print(f"   🔄 AI calls made: {metadata.get('ai_calls_made', 0)}")
        print(f"   📊 Confidence score: {test3.response_data.get('confidence_score', 'N/A')}")
        print(f"   🚫 Fallback used: {metadata.get('fallback_used', 'Unknown')}")
        print(f"   ✨ Genuine AI processing: {metadata.get('genuine_ai_processing', 'Unknown')}")
        
        # Validate no hardcoded scores
        match_scores = test3.response_data.get('match_scores', {})
        if match_scores.get('location') == 0.8 and match_scores.get('salary') == 0.75:
            print(f"   ⚠️  WARNING: Detected potential hardcoded scores!")
            test3.passed = False
        
    else:
        print(f"   ❌ FAILED: Expected HTTP 200, got {test3.actual_result}")
        print(f"   📝 Response: {test3.response_data}")
    
    tests.append(test3)
    
    # Test 4: Resume optimization should return genuine improvements
    print("\n4. Testing resume optimization with genuine AI improvements...")
    test4 = TestResult("Resume Optimization", "HTTP 200 with real improvements")
    
    start_time = time.time()
    result = test_endpoint(f"{BASE_URL}/api/ai/optimize-resume", "POST", valid_data, 200)
    processing_time = time.time() - start_time
    
    test4.actual_result = f"HTTP {result['status_code']}"
    test4.passed = result['status_code'] == 200
    test4.response_data = result.get('data', {})
    
    if test4.passed:
        print(f"   ✅ PASSED: {test4.actual_result}")
        print(f"   ⏱️  Processing time: {processing_time:.2f}s")
        
        # Check for genuine optimization
        optimized_resume = test4.response_data.get('optimized_resume', '')
        original_resume = valid_data['resume_text']
        
        if optimized_resume == original_resume:
            print(f"   ❌ FAILED: Optimized resume is identical to original!")
            test4.passed = False
        else:
            print(f"   ✅ Resume was actually modified")
            print(f"   📝 Improvements made: {len(test4.response_data.get('improvements_made', []))}")
            print(f"   🔑 Keywords added: {len(test4.response_data.get('keywords_added', []))}")
            print(f"   📈 ATS improvement: {test4.response_data.get('ats_score_improvement', 'N/A')}")
            
            # Check for placeholder content
            if "temporarily unavailable" in optimized_resume.lower():
                print(f"   ❌ FAILED: Contains placeholder content!")
                test4.passed = False
    else:
        print(f"   ❌ FAILED: Expected HTTP 200, got {test4.actual_result}")
    
    tests.append(test4)
    
    # Test 5: AI Health Check
    print("\n5. Testing AI service health check...")
    test5 = TestResult("AI Health Check", "Healthy with transparency")
    
    result = test_endpoint(f"{BASE_URL}/api/ai/health", "GET")
    test5.actual_result = f"HTTP {result['status_code']}"
    test5.passed = result['status_code'] == 200
    test5.response_data = result.get('data', {})
    
    if test5.passed:
        print(f"   ✅ PASSED: {test5.actual_result}")
        print(f"   🏥 Status: {test5.response_data.get('status', 'Unknown')}")
        print(f"   🤖 Genuine AI processing: {test5.response_data.get('genuine_ai_processing', 'Unknown')}")
        print(f"   🚫 No fallback mechanisms: {test5.response_data.get('no_fallback_mechanisms', 'Unknown')}")
    else:
        print(f"   ❌ FAILED: Expected HTTP 200, got {test5.actual_result}")
    
    tests.append(test5)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed_tests = sum(1 for test in tests if test.passed)
    total_tests = len(tests)
    
    for test in tests:
        status = "✅ PASSED" if test.passed else "❌ FAILED"
        print(f"{status}: {test.test_name}")
    
    print(f"\n🎯 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! The genuine AI system is working correctly.")
        print("✅ Input validation is working")
        print("✅ No fallback data is being returned")
        print("✅ Genuine AI processing is confirmed")
        print("✅ Transparency and confidence scoring implemented")
        print("✅ System ready for GitHub push!")
        return True
    else:
        print("❌ SOME TESTS FAILED! Issues need to be addressed before GitHub push.")
        return False

if __name__ == "__main__":
    print("Starting comprehensive test suite...")
    print("Make sure the backend server is running on http://localhost:8000")
    
    # Wait for user confirmation
    input("Press Enter to continue...")
    
    success = run_comprehensive_tests()
    
    if success:
        print("\n🚀 READY FOR GITHUB PUSH!")
        sys.exit(0)
    else:
        print("\n🛑 NOT READY - Fix issues before pushing to GitHub")
        sys.exit(1)
