"""
Basic tests that don't require complex dependencies
"""

import pytest
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_python_version():
    """Test that we're running Python 3.8+"""
    assert sys.version_info >= (3, 8), f"Python version {sys.version_info} is too old"


def test_imports():
    """Test that basic imports work"""
    try:
        import fastapi
        import uvicorn
        import openai
        import pytest
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_main_module_exists():
    """Test that main.py exists and can be imported"""
    try:
        import main
        assert hasattr(main, 'app'), "main.py should have an 'app' variable"
    except ImportError as e:
        pytest.fail(f"Cannot import main.py: {e}")


def test_app_services_exist():
    """Test that service modules exist"""
    service_files = [
        "app/services/enhanced_ai_service.py",
        "app/services/ai_service.py",
        "app/services/enterprise_ats_service.py"
    ]
    
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for service_file in service_files:
        service_path = os.path.join(backend_dir, service_file)
        assert os.path.exists(service_path), f"Service file {service_file} does not exist"


def test_requirements_file_exists():
    """Test that requirements.txt exists"""
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    requirements_path = os.path.join(backend_dir, "requirements.txt")
    assert os.path.exists(requirements_path), "requirements.txt does not exist"


def test_basic_math():
    """Basic test to ensure pytest is working"""
    assert 2 + 2 == 4
    assert 10 / 2 == 5
    assert 3 * 3 == 9


class TestBasicFunctionality:
    """Test class for basic functionality"""
    
    def test_string_operations(self):
        """Test basic string operations"""
        test_string = "Recruitly AI Resume Optimizer"
        assert "Recruitly" in test_string
        assert test_string.lower() == "recruitly ai resume optimizer"
        assert len(test_string) > 0
    
    def test_list_operations(self):
        """Test basic list operations"""
        test_list = ["backend", "frontend", "ai", "testing"]
        assert len(test_list) == 4
        assert "testing" in test_list
        assert test_list[0] == "backend"
    
    def test_dict_operations(self):
        """Test basic dictionary operations"""
        test_dict = {
            "status": "healthy",
            "version": "1.0.0",
            "mode": "development"
        }
        assert test_dict["status"] == "healthy"
        assert "version" in test_dict
        assert len(test_dict.keys()) == 3


@pytest.mark.asyncio
async def test_async_functionality():
    """Test that async functionality works"""
    async def async_function():
        return "async_result"
    
    result = await async_function()
    assert result == "async_result"


def test_file_structure():
    """Test that expected files and directories exist"""
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    expected_files = [
        "main.py",
        "requirements.txt",
        "pytest.ini"
    ]
    
    expected_dirs = [
        "app",
        "app/services",
        "tests"
    ]
    
    for file_name in expected_files:
        file_path = os.path.join(backend_dir, file_name)
        assert os.path.exists(file_path), f"Expected file {file_name} does not exist"
    
    for dir_name in expected_dirs:
        dir_path = os.path.join(backend_dir, dir_name)
        assert os.path.exists(dir_path), f"Expected directory {dir_name} does not exist"


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
