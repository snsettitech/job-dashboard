#!/usr/bin/env python3
"""
Quick verification script to test infrastructure fixes
Run this to verify all components are properly integrated
"""

import asyncio
import sys
import os
from pathlib import Path

async def test_router_imports():
    """Test that all routers can be imported"""
    print("🔍 Testing router imports...")
    
    try:
        # Add backend to path
        backend_path = Path(__file__).parent.parent / "backend"
        sys.path.insert(0, str(backend_path))
        
        from app.routers import ai_routes
        from app.routers import metrics_routes
        print("✅ All routers import successfully")
        return True
    except Exception as e:
        print(f"❌ Router import failed: {e}")
        return False

async def test_metrics_service():
    """Test metrics service functionality"""
    print("🔍 Testing metrics service...")
    
    try:
        from app.services.metrics_service import MetricsService
        
        # Create test service
        test_service = MetricsService(storage_path="test_metrics")
        
        # Test recording event
        await test_service.record_event(
            event_type="test_event",
            data={"test": "data"},
            user_id="test_user"
        )
        
        # Test getting summary
        summary = await test_service.get_metrics_summary(days_back=1)
        
        print(f"✅ Metrics service working - recorded {summary.total_events} events")
        
        # Cleanup
        import shutil
        if Path("test_metrics").exists():
            shutil.rmtree("test_metrics")
        
        return True
    except Exception as e:
        print(f"❌ Metrics service test failed: {e}")
        return False

async def test_file_structure():
    """Test that all expected files exist"""
    print("🔍 Testing file structure...")
    
    base_path = Path(__file__).parent.parent
    expected_files = [
        ".pre-commit-config.yaml",
        ".commitlintrc.js",
        ".gitmessage",
        ".github/workflows/ci-cd.yml",
        ".husky/commit-msg",
        ".husky/pre-commit",
        "backend/app/services/metrics_service.py",
        "backend/app/routers/metrics_routes.py",
        "frontend/src/services/metrics.ts",
        "tests/integration/test_full_workflow.py",
        "scripts/dev.ps1",
        "scripts/setup-git-hooks.ps1"
    ]
    
    missing_files = []
    for file_path in expected_files:
        full_path = base_path / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All expected files present")
        return True

async def test_config_validity():
    """Test configuration file validity"""
    print("🔍 Testing configuration validity...")
    
    try:
        base_path = Path(__file__).parent.parent
        
        # Test YAML validity
        import yaml
        with open(base_path / ".pre-commit-config.yaml") as f:
            yaml.safe_load(f)
        
        with open(base_path / ".github/workflows/ci-cd.yml") as f:
            yaml.safe_load(f)
        
        # Test JavaScript validity (basic syntax check)
        commitlint_path = base_path / ".commitlintrc.js"
        if commitlint_path.exists():
            with open(commitlint_path) as f:
                content = f.read()
                if "module.exports" in content:
                    print("✅ Configuration files are valid")
                    return True
        
        return False
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

async def main():
    """Run all verification tests"""
    print("🚀 Infrastructure Verification Tests")
    print("=" * 40)
    
    tests = [
        test_file_structure,
        test_config_validity,
        test_router_imports,
        test_metrics_service
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
        print()
    
    passed = sum(results)
    total = len(results)
    
    print("=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All infrastructure components verified successfully!")
        print("\n✅ Ready for:")
        print("   - Git commits with conventional format")
        print("   - Pre-commit hooks with code quality checks")
        print("   - CI/CD pipeline with comprehensive testing")
        print("   - Metrics collection and monitoring")
        print("   - Integration testing with proper endpoints")
        return 0
    else:
        print("❌ Some components need attention")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
