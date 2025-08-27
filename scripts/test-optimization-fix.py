#!/usr/bin/env python3
"""
Test script to verify the resume optimization KeyError fix
"""

import requests
import json
import time

def test_resume_optimization():
    """Test the resume optimization endpoint specifically"""
    print("🔧 TESTING RESUME OPTIMIZATION FIX")
    print("=" * 50)
    
    # Test data
    test_data = {
        "resume_text": "Senior Software Engineer with 8 years of experience in Python, Django, React, and AWS. Led development teams of 5+ engineers, architected scalable microservices handling 1M+ daily requests, and implemented CI/CD pipelines reducing deployment time by 60%. Expert in database optimization, API design, and agile methodologies. Developed RESTful APIs serving 100K+ users daily. Managed cloud infrastructure on AWS with 99.9% uptime. Mentored junior developers and conducted code reviews.",
        "job_description": "We are seeking a Senior Software Engineer to join our growing engineering team. The ideal candidate will have 5+ years of experience in Python and React development, with strong leadership skills and experience with cloud platforms like AWS. Responsibilities include architecting scalable systems, mentoring junior developers, and collaborating with cross-functional teams to deliver high-quality software solutions. Requirements: Bachelor's degree in Computer Science, proficiency in Python and JavaScript, experience with microservices architecture, and excellent communication skills. Must have experience with Docker, Kubernetes, and CI/CD pipelines."
    }
    
    print("1. Testing resume optimization endpoint...")
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:8000/api/ai/optimize-resume",
            headers={"Content-Type": "application/json"},
            data=json.dumps(test_data),
            timeout=45
        )
        processing_time = time.time() - start_time
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Processing Time: {processing_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS: Resume optimization completed")
            
            # Check for required fields
            required_fields = [
                "optimized_resume", "improvements_made", "keywords_added", 
                "ats_score_improvement", "confidence_score", "confidence_level",
                "confidence_interval", "processing_metadata"
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in result:
                    missing_fields.append(field)
                else:
                    print(f"   ✅ {field}: {type(result[field]).__name__}")
            
            if missing_fields:
                print(f"   ❌ Missing fields: {missing_fields}")
                return False
            else:
                print("   ✅ All required fields present")
                
                # Show key results
                print(f"   📊 Confidence Score: {result['confidence_score']}")
                print(f"   📈 Confidence Level: {result['confidence_level']}")
                print(f"   📝 Improvements Made: {len(result['improvements_made'])}")
                print(f"   🔑 Keywords Added: {len(result['keywords_added'])}")
                print(f"   📈 ATS Improvement: {result['ats_score_improvement']}")
                
                return True
        else:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'No detail')}")
            except:
                print(f"   Raw response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_upload_optimization():
    """Test the upload-analyze-optimize endpoint that was failing"""
    print("\n2. Testing upload-analyze-optimize endpoint...")
    
    # Create a simple test file
    test_resume_content = """John Doe
Senior Software Engineer

Experience:
- Software Engineer at TechCorp (2020-2024)
- Developed web applications using Python and React
- Worked with databases and APIs
- Led a team of 3 developers

Skills:
- Python, JavaScript, React, Django
- AWS, Docker, Git
- Database design, API development

Education:
- Bachelor's in Computer Science, State University (2020)
"""
    
    test_job_description = """We are seeking a Senior Software Engineer to join our growing engineering team. The ideal candidate will have 5+ years of experience in Python and React development, with strong leadership skills and experience with cloud platforms like AWS. Responsibilities include architecting scalable systems, mentoring junior developers, and collaborating with cross-functional teams to deliver high-quality software solutions. Requirements: Bachelor's degree in Computer Science, proficiency in Python and JavaScript, experience with microservices architecture, and excellent communication skills."""
    
    try:
        # Create form data
        files = {'file': ('test_resume.txt', test_resume_content, 'text/plain')}
        data = {
            'job_description': test_job_description,
            'company_name': 'Test Company',
            'job_title': 'Senior Software Engineer'
        }
        
        start_time = time.time()
        response = requests.post(
            "http://localhost:8000/api/ai/upload-analyze-optimize",
            files=files,
            data=data,
            timeout=60
        )
        processing_time = time.time() - start_time
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Processing Time: {processing_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS: Upload optimization completed")
            
            # Check for the specific fields that were causing KeyError
            optimization = result.get("optimization", {})
            if "confidence_score" in optimization:
                print(f"   ✅ confidence_score: {optimization['confidence_score']}")
            else:
                print("   ❌ Missing confidence_score in optimization")
                return False
                
            if "confidence_level" in optimization:
                print(f"   ✅ confidence_level: {optimization['confidence_level']}")
            else:
                print("   ❌ Missing confidence_level in optimization")
                return False
            
            print(f"   📊 Optimization confidence: {optimization.get('confidence_score', 'N/A')}")
            print(f"   📈 Match confidence: {result.get('job_match_analysis', {}).get('confidence_score', 'N/A')}")
            
            return True
        else:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'No detail')}")
            except:
                print(f"   Raw response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def run_all_tests():
    """Run all optimization tests"""
    print("🧪 RESUME OPTIMIZATION KEYERROR FIX TEST")
    print("=" * 60)
    
    tests = [
        ("Resume Optimization Endpoint", test_resume_optimization),
        ("Upload-Analyze-Optimize Endpoint", test_upload_optimization)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! KeyError fix is working correctly.")
        print("✅ confidence_score field present")
        print("✅ confidence_level field present") 
        print("✅ Resume optimization working")
        print("✅ Upload optimization working")
        return True
    else:
        print("❌ Some tests failed. KeyError issue may persist.")
        return False

if __name__ == "__main__":
    print("Starting resume optimization KeyError fix test...")
    print("Make sure the backend server is running on http://localhost:8000")
    
    # Wait for user confirmation
    input("Press Enter to continue...")
    
    success = run_all_tests()
    
    if success:
        print("\n🚀 KEYERROR FIX VERIFIED - Resume optimization working!")
    else:
        print("\n🛑 ISSUES DETECTED - Please review the errors above")
