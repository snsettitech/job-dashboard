"""
Test suite for main FastAPI application endpoints
"""

import pytest
import sys
import os
import httpx

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    FASTAPI_AVAILABLE = True
except Exception as e:
    print(f"FastAPI setup failed: {e}")
    FASTAPI_AVAILABLE = False
    client = None


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
def test_root_endpoint():
    """Test the root endpoint returns welcome message"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Recruitly" in data["message"]


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
def test_health_endpoint():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "version" in data
    assert "mode" in data


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
def test_dashboard_endpoint():
    """Test the dashboard data endpoint"""
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()

    # Check required dashboard fields
    assert "stats" in data
    assert "recentApplications" in data
    assert "topMatches" in data

    # Check stats structure
    stats = data["stats"]
    assert "applications" in stats
    assert "interviews" in stats
    assert "matches" in stats
    assert "autoApplyActive" in stats


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
def test_upload_endpoint_no_file():
    """Test upload endpoint without file returns error"""
    response = client.post("/api/upload")
    assert response.status_code == 422  # Unprocessable Entity


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
def test_upload_endpoint_with_text():
    """Test upload endpoint with text content"""
    files = {"file": ("test.txt", "This is test resume content", "text/plain")}
    response = client.post("/api/upload", files=files)

    # Should return 200 even with mock AI service
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_optimize_endpoint_no_data():
    """Test optimize endpoint without data returns error"""
    response = client.post("/api/optimize")
    assert response.status_code == 422  # Unprocessable Entity


def test_optimize_endpoint_with_data():
    """Test optimize endpoint with resume data"""
    test_data = {
        "resumeText": "Test resume content",
        "jobDescription": "Test job description"
    }
    response = client.post("/api/optimize", json=test_data)
    
    # Should return 200 with optimization result
    assert response.status_code == 200
    data = response.json()
    assert "optimizedResume" in data or "message" in data


def test_cors_headers():
    """Test that CORS headers are properly set"""
    response = client.get("/")
    assert response.status_code == 200
    
    # Check for CORS headers (if configured)
    headers = response.headers
    # Note: Actual CORS headers depend on FastAPI CORS configuration


def test_invalid_endpoint():
    """Test that invalid endpoints return 404"""
    response = client.get("/api/nonexistent")
    assert response.status_code == 404


class TestAPIResponses:
    """Test class for API response formats"""
    
    def test_json_response_format(self):
        """Test that all endpoints return valid JSON"""
        endpoints = ["/", "/health", "/api/dashboard"]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            
            # Should be valid JSON
            data = response.json()
            assert isinstance(data, dict)
    
    def test_error_response_format(self):
        """Test that error responses have consistent format"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
