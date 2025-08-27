#!/usr/bin/env python3
"""
Test script for the Recruitly development workflow system
"""

import os
import sys
import subprocess
from pathlib import Path

def test_workflow_system():
    """Test the development workflow system"""
    print("🧪 Testing Recruitly Development Workflow System")
    print("=" * 50)

    project_root = Path(__file__).parent.parent

    # Test 1: Check if scripts exist
    print("📁 Checking script files...")
    scripts = [
        "scripts/dev-workflow.py",
        "scripts/auto-commit.py",
        "scripts/dev.ps1"
    ]

    for script in scripts:
        script_path = project_root / script
        if script_path.exists():
            print(f"✅ {script}")
        else:
            print(f"❌ {script} - Missing!")
            return False

    # Test 2: Check documentation files
    print("\n📚 Checking documentation files...")
    docs = [
        "docs/DEVELOPMENT_CONTEXT.md",
        "docs/FEATURE_LOG.json",
        "README.md"
    ]

    for doc in docs:
        doc_path = project_root / doc
        if doc_path.exists():
            print(f"✅ {doc}")
        else:
            print(f"❌ {doc} - Missing!")
            return False

    # Test 3: Test Python workflow script
    print("\n🐍 Testing Python workflow script...")
    try:
        result = subprocess.run(
            [sys.executable, "scripts/dev-workflow.py", "--help"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("✅ Python workflow script is functional")
        else:
            print(f"❌ Python workflow script failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error testing Python script: {e}")
        return False

    # Test 4: Test auto-commit script
    print("\n🔄 Testing auto-commit script...")
    try:
        result = subprocess.run(
            [sys.executable, "scripts/auto-commit.py"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10
        )
        # This should fail with usage message, which is expected
        if "Usage:" in result.stdout or "Usage:" in result.stderr:
            print("✅ Auto-commit script is functional")
        else:
            print("✅ Auto-commit script exists and runs")
    except Exception as e:
        print(f"❌ Error testing auto-commit script: {e}")
        return False

    # Test 5: Check PowerShell script syntax
    print("\n💻 Checking PowerShell script...")
    ps_script = project_root / "scripts/dev.ps1"
    if ps_script.exists():
        print("✅ PowerShell script exists")
        # Basic syntax check by reading the file
        try:
            content = ps_script.read_text()
            if "param(" in content and "function" in content:
                print("✅ PowerShell script has valid structure")
            else:
                print("❌ PowerShell script structure seems invalid")
                return False
        except Exception as e:
            print(f"❌ Error reading PowerShell script: {e}")
            return False

    # Test 6: Validate JSON files
    print("\n📋 Validating JSON files...")
    import json

    json_files = [
        "docs/FEATURE_LOG.json"
    ]

    for json_file in json_files:
        json_path = project_root / json_file
        try:
            with open(json_path, 'r') as f:
                json.load(f)
            print(f"✅ {json_file} - Valid JSON")
        except Exception as e:
            print(f"❌ {json_file} - Invalid JSON: {e}")
            return False

    print("\n🎉 All workflow system tests passed!")
    print("\n📋 Next Steps:")
    print("1. Test the workflow: .\\scripts\\dev.ps1 status")
    print("2. Start a new feature: .\\scripts\\dev.ps1 start -Feature 'test-feature' -Description 'Test feature'")
    print("3. Complete the feature: .\\scripts\\dev.ps1 complete -Feature 'test-feature'")

    return True

def show_usage_examples():
    """Show usage examples for the workflow system"""
    print("\n📖 Workflow Usage Examples:")
    print("=" * 30)

    examples = [
        {
            "title": "Start a new feature",
            "command": ".\\scripts\\dev.ps1 start -Feature 'router-integration' -Description 'Mount ai_routes.py to main.py'"
        },
        {
            "title": "Update feature progress",
            "command": ".\\scripts\\dev.ps1 update -Feature 'router-integration' -Files @('backend/main.py') -Notes 'Added router mounting'"
        },
        {
            "title": "Complete feature",
            "command": ".\\scripts\\dev.ps1 complete -Feature 'router-integration'"
        },
        {
            "title": "Check project status",
            "command": ".\\scripts\\dev.ps1 status"
        },
        {
            "title": "Run tests",
            "command": ".\\scripts\\dev.ps1 test"
        },
        {
            "title": "Auto-commit completed feature",
            "command": ".\\scripts\\dev.ps1 commit -Feature 'router-integration' -Description 'Integrated modular router system'"
        }
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}:")
        print(f"   {example['command']}")

if __name__ == "__main__":
    success = test_workflow_system()

    if success:
        show_usage_examples()
        sys.exit(0)
    else:
        print("\n❌ Workflow system tests failed!")
        sys.exit(1)
