#!/usr/bin/env python3
"""
Simple test script to verify input validation is working
"""

import requests
import json

def test_validation():
    print("🧪 TESTING INPUT VALIDATION")
    print("=" * 50)
    
    # Test 1: Gibberish input
    print("\n1. Testing gibberish input rejection...")
    data1 = {
        "resume_text": "Software Engineer with 5 years experience in Python and React development.",
        "job_description": "ssssssssss"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/ai/analyze-match",
            headers={"Content-Type": "application/json"},
            data=json.dumps(data1),
            timeout=15
        )
        
        if response.status_code == 400:
            print("✅ SUCCESS: Gibberish input rejected with HTTP 400")
            try:
                error_detail = response.json().get("detail", "No detail provided")
                print(f"   📝 Error message: {error_detail}")
            except:
                print(f"   📝 Raw response: {response.text}")
        else:
            print(f"❌ FAILED: Expected HTTP 400, got {response.status_code}")
            print(f"   📝 Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 2: Too short input
    print("\n2. Testing insufficient length rejection...")
    data2 = {
        "resume_text": "Software Engineer with 5 years experience in Python and React development.",
        "job_description": "looking for someone"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/ai/analyze-match",
            headers={"Content-Type": "application/json"},
            data=json.dumps(data2),
            timeout=15
        )
        
        if response.status_code == 400:
            print("✅ SUCCESS: Short input rejected with HTTP 400")
            try:
                error_detail = response.json().get("detail", "No detail provided")
                print(f"   📝 Error message: {error_detail}")
            except:
                print(f"   📝 Raw response: {response.text}")
        else:
            print(f"❌ FAILED: Expected HTTP 400, got {response.status_code}")
            print(f"   📝 Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 3: Valid input should work
    print("\n3. Testing valid input processing...")
    data3 = {
        "resume_text": "Senior Software Engineer with 8 years of experience in Python, Django, React, and AWS. Led development teams of 5+ engineers, architected scalable microservices handling 1M+ daily requests, and implemented CI/CD pipelines reducing deployment time by 60%. Expert in database optimization, API design, and agile methodologies.",
        "job_description": "We are seeking a Senior Software Engineer to join our growing engineering team. The ideal candidate will have 5+ years of experience in Python and React development, with strong leadership skills and experience with cloud platforms like AWS. Responsibilities include architecting scalable systems, mentoring junior developers, and collaborating with cross-functional teams to deliver high-quality software solutions. Requirements: Bachelor's degree in Computer Science, proficiency in Python and JavaScript, experience with microservices architecture, and excellent communication skills."
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/ai/analyze-match",
            headers={"Content-Type": "application/json"},
            data=json.dumps(data3),
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ SUCCESS: Valid input processed with HTTP 200")
            try:
                result = response.json()
                print(f"   📊 Match scores: {result.get('match_scores', 'N/A')}")
                print(f"   🤖 Processing metadata: {result.get('processing_metadata', 'N/A')}")
            except:
                print(f"   📝 Raw response: {response.text[:200]}")
        else:
            print(f"❌ FAILED: Expected HTTP 200, got {response.status_code}")
            print(f"   📝 Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 VALIDATION TEST COMPLETED")

if __name__ == "__main__":
    test_validation()
