#!/usr/bin/env python3
"""
Quick diagnostic script to test AI functionality fixes
"""

import os
import sys

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Prevent main.py from auto-starting server
os.environ["SKIP_SERVER_START"] = "1"


def test_imports():
    """Test all critical imports"""
    print("🔍 Testing imports...")

    try:
        import numpy as np

        print(f"✅ numpy {np.__version__}")
    except Exception as e:
        print(f"❌ numpy import failed: {e}")
        return False

    try:
        from sklearn.metrics.pairwise import cosine_similarity

        print("✅ sklearn imports working")
    except Exception as e:
        print(f"❌ sklearn import failed: {e}")
        return False

    try:
        import openai

        print(f"✅ openai {openai.__version__}")
    except Exception as e:
        print(f"❌ openai import failed: {e}")
        return False

    return True


def test_openai_key():
    """Test OpenAI API key configuration"""
    print("\n🔑 Testing OpenAI API key...")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OpenAI API key found in environment")
        return False

    if api_key.startswith("REMOVEDproj-"):
        print("❌ API key still has 'REMOVED' prefix")
        return False

    if not api_key.startswith("proj-"):
        print("❌ API key doesn't start with 'proj-' (invalid format)")
        return False

    print(f"✅ API key format looks correct: {api_key[:15]}...")
    return True


def test_ai_service():
    """Test AI service initialization"""
    print("\n🤖 Testing AI service...")

    try:
        from app.services.ai_service import AIService

        ai_service = AIService()
        print("✅ AIService initialized successfully")
        return True
    except Exception as e:
        print(f"❌ AIService initialization failed: {e}")
        return False


def test_enhanced_ai_service():
    """Test Enhanced AI service initialization"""
    print("\n⚡ Testing Enhanced AI service...")

    try:
        from app.services.enhanced_ai_service import EnhancedAIService

        enhanced_ai = EnhancedAIService()
        print("✅ EnhancedAIService initialized successfully")
        return True
    except Exception as e:
        print(f"❌ EnhancedAIService initialization failed: {e}")
        return False


def test_router_imports():
    """Test router imports"""
    print("\n🔗 Testing router imports...")

    try:
        from app.routers import ai_routes

        print("✅ AI routes imported successfully")
        return True
    except Exception as e:
        print(f"❌ AI routes import failed: {e}")
        return False


def main():
    """Run all diagnostic tests"""
    print("🚀 Recruitly AI Diagnostic Tool")
    print("=" * 40)

    tests = [
        ("Import Tests", test_imports),
        ("OpenAI Key Test", test_openai_key),
        ("AI Service Test", test_ai_service),
        ("Enhanced AI Service Test", test_enhanced_ai_service),
        ("Router Import Test", test_router_imports),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 40)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 40)

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\nResults: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("\n🎉 All tests passed! AI functionality should work.")
    else:
        print(
            f"\n⚠️ {len(results) - passed} tests failed. AI functionality may not work properly."
        )

    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
