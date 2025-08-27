"""
Quick fix for AI issues
"""

import os
import sys


def main():
    print("🔧 RECRUITLY AI QUICK FIX")
    print("=" * 30)

    # Check .env file
    print("\n1. Checking .env file...")
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            content = f.read()

        if "OPENAI_API_KEY=proj-" in content:
            print("✅ .env file has correct API key format")
        elif "REMOVEDproj-" in content:
            print("❌ .env file still has REMOVED prefix")
            # Fix it
            content = content.replace(
                'OPENAI_API_KEY= "REMOVEDproj-', "OPENAI_API_KEY=proj-"
            )
            content = content.replace('"', "")
            with open(".env", "w") as f:
                f.write(content)
            print("✅ Fixed .env file")
        else:
            print("❌ .env file format issue")
    else:
        print("❌ No .env file found")

    # Check imports
    print("\n2. Testing critical imports...")

    try:
        import numpy as np

        print(f"✅ numpy {np.__version__}")
    except Exception as e:
        print(f"❌ numpy failed: {e}")
        return False

    try:
        from sklearn.metrics.pairwise import cosine_similarity

        print("✅ sklearn working")
    except Exception as e:
        print(f"❌ sklearn failed: {e}")
        return False

    try:
        import openai

        print(f"✅ openai {openai.__version__}")
    except Exception as e:
        print(f"❌ openai failed: {e}")
        return False

    print("\n3. Testing environment loading...")
    try:
        from dotenv import load_dotenv

        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key.startswith("proj-"):
            print(f"✅ API key loaded correctly: {api_key[:15]}...")
        else:
            print(f"❌ API key issue: {api_key[:20] if api_key else 'None'}...")
            return False
    except Exception as e:
        print(f"❌ Environment loading failed: {e}")
        return False

    print("\n🎉 All checks passed! AI should work now.")
    print("\n📋 Next steps:")
    print("1. Stop your current server (Ctrl+C)")
    print("2. Restart with: python main.py")
    print("3. Test AI optimization in the frontend")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
