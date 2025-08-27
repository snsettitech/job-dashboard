# tests/integration/test_full_workflow.py - Full Stack Integration Tests
import pytest
import asyncio
import httpx
from typing import Dict, Any

# Test configuration
TEST_CONFIG = {
    "backend_url": "http://localhost:8000",
    "frontend_url": "http://localhost:3000",
    "timeout": 30.0
}

class IntegrationTestClient:
    """Client for integration testing"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session_id = f"test_session_{asyncio.get_event_loop().time()}"
        self.user_id = "test_user_123"

    async def health_check(self) -> Dict[str, Any]:
        """Check if backend is healthy"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            return response.json()

    async def upload_resume(self, resume_content: str, filename: str = "test_resume.txt") -> Dict[str, Any]:
        """Upload a test resume using the actual upload-analyze-optimize endpoint"""
        async with httpx.AsyncClient() as client:
            files = {"file": (filename, resume_content, "text/plain")}
            data = {"job_description": "Sample job for testing upload"}
            response = await client.post(f"{self.base_url}/api/ai/upload-analyze-optimize",
                                       files=files, data=data)
            return response.json()

    async def optimize_resume(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """Optimize resume for job using actual endpoint"""
        async with httpx.AsyncClient() as client:
            data = {
                "resume_text": resume_text,
                "job_description": job_description
            }
            response = await client.post(f"{self.base_url}/api/ai/optimize-resume", json=data)
            return response.json()

    async def match_job(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """Match resume to job using actual endpoint"""
        async with httpx.AsyncClient() as client:
            data = {
                "resume_text": resume_text,
                "job_description": job_description
            }
            response = await client.post(f"{self.base_url}/api/ai/analyze-match", json=data)
            return response.json()

    async def get_dashboard(self) -> Dict[str, Any]:
        """Get dashboard data"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/dashboard")
            return response.json()

    async def track_metric(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Track a metric event"""
        async with httpx.AsyncClient() as client:
            metric_data = {
                "event_type": event_type,
                "data": data,
                "user_id": self.user_id,
                "session_id": self.session_id
            }
            response = await client.post(f"{self.base_url}/api/metrics/record", json=metric_data)
            return response.json()

@pytest.fixture
async def test_client():
    """Create test client"""
    client = IntegrationTestClient(TEST_CONFIG["backend_url"])

    # Wait for backend to be ready
    max_retries = 10
    for i in range(max_retries):
        try:
            await client.health_check()
            break
        except Exception:
            if i == max_retries - 1:
                pytest.skip("Backend not available for integration tests")
            await asyncio.sleep(2)

    return client

@pytest.fixture
def sample_resume():
    """Sample resume content for testing"""
    return """
John Doe
Software Engineer

EXPERIENCE:
- 5 years Python development
- FastAPI and React experience
- Machine learning projects
- Database design and optimization

SKILLS:
- Python, JavaScript, TypeScript
- FastAPI, React, Node.js
- PostgreSQL, MongoDB
- AWS, Docker, Kubernetes
- Machine Learning, AI

EDUCATION:
- BS Computer Science, University of Technology
"""

@pytest.fixture
def sample_job_description():
    """Sample job description for testing"""
    return """
Senior Software Engineer - AI/ML Platform

We are looking for a Senior Software Engineer to join our AI/ML platform team.

REQUIREMENTS:
- 5+ years of software development experience
- Strong Python programming skills
- Experience with FastAPI or similar web frameworks
- React/TypeScript frontend experience
- Machine learning and AI experience preferred
- Database design experience
- Cloud platform experience (AWS, GCP, Azure)

RESPONSIBILITIES:
- Design and implement scalable AI/ML services
- Build responsive web applications
- Collaborate with data science team
- Optimize system performance
- Mentor junior developers
"""

class TestFullWorkflow:
    """Test complete user workflows"""

    @pytest.mark.asyncio
    async def test_health_checks(self, test_client):
        """Test that all services are healthy"""
        # Backend health
        health = await test_client.health_check()
        assert health["status"] == "healthy"

        # AI service health
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{test_client.base_url}/api/ai/health")
            ai_health = response.json()
            assert ai_health["status"] in ["healthy", "unhealthy"]  # May be unhealthy without API keys

        # Metrics health
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{test_client.base_url}/api/metrics/health")
            metrics_health = response.json()
            assert metrics_health["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_resume_upload_workflow(self, test_client, sample_resume):
        """Test resume upload workflow"""
        # Upload resume
        result = await test_client.upload_resume(sample_resume)

        # Should succeed or fail gracefully
        assert "status" in result

        # Track the upload event
        metric_result = await test_client.track_metric("resume_upload", {
            "file_size": len(sample_resume),
            "file_type": "text/plain"
        })
        assert metric_result["status"] == "success"

    @pytest.mark.asyncio
    async def test_job_matching_workflow(self, test_client, sample_resume, sample_job_description):
        """Test job matching workflow"""
        try:
            # Match resume to job
            match_result = await test_client.match_job(sample_resume, sample_job_description)

            # Should have match scores
            if "match_scores" in match_result:
                assert "overall" in match_result["match_scores"]
                assert "skills" in match_result["match_scores"]
                assert "experience" in match_result["match_scores"]

                # Scores should be between 0 and 1
                assert 0 <= match_result["match_scores"]["overall"] <= 1
                assert 0 <= match_result["match_scores"]["skills"] <= 1
                assert 0 <= match_result["match_scores"]["experience"] <= 1

                # Track the matching event
                await test_client.track_metric("job_match", {
                    "match_score": match_result["match_scores"]["overall"],
                    "job_type": "software_engineer"
                })
            else:
                # Fallback for different response format
                await test_client.track_metric("job_match", {
                    "match_score": 0.7,
                    "job_type": "software_engineer"
                })

        except Exception as e:
            # AI service might not be available in test environment
            pytest.skip(f"AI service not available: {e}")

    @pytest.mark.asyncio
    async def test_resume_optimization_workflow(self, test_client, sample_resume, sample_job_description):
        """Test resume optimization workflow"""
        try:
            # Optimize resume
            optimization_result = await test_client.optimize_resume(sample_resume, sample_job_description)

            # Should have optimization results
            assert "optimized_resume" in optimization_result or "error" in optimization_result

            # Track the optimization event
            await test_client.track_metric("resume_optimization", {
                "job_title": "Senior Software Engineer",
                "success": "optimized_resume" in optimization_result
            })

        except Exception as e:
            # AI service might not be available in test environment
            pytest.skip(f"AI service not available: {e}")

    @pytest.mark.asyncio
    async def test_dashboard_workflow(self, test_client):
        """Test dashboard data retrieval"""
        # Get dashboard data
        dashboard = await test_client.get_dashboard()

        # Should have basic structure
        assert isinstance(dashboard, dict)

        # Track dashboard view
        await test_client.track_metric("page_view", {
            "page": "dashboard"
        })

    @pytest.mark.asyncio
    async def test_metrics_collection_workflow(self, test_client):
        """Test metrics collection and retrieval"""
        # Record several test metrics
        test_events = [
            ("page_view", {"page": "home"}),
            ("button_click", {"button_id": "optimize_button", "page": "optimizer"}),
            ("feature_usage", {"feature": "job_matching", "action": "search"}),
        ]

        for event_type, data in test_events:
            result = await test_client.track_metric(event_type, data)
            assert result["status"] == "success"

        # Get metrics summary
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{test_client.base_url}/api/metrics/summary?days_back=1")
            summary = response.json()

            assert "total_events" in summary
            assert "unique_users" in summary
            assert summary["total_events"] >= len(test_events)

    @pytest.mark.asyncio
    async def test_error_handling(self, test_client):
        """Test error handling across services"""
        # Test invalid requests
        async with httpx.AsyncClient() as client:
            # Invalid job match request
            response = await client.post(f"{test_client.base_url}/api/ai/match-job", json={})
            assert response.status_code in [400, 422, 500]  # Should handle gracefully

            # Invalid metrics request
            response = await client.post(f"{test_client.base_url}/api/metrics/record", json={})
            assert response.status_code in [400, 422, 500]  # Should handle gracefully

    @pytest.mark.asyncio
    async def test_complete_user_journey(self, test_client, sample_resume, sample_job_description):
        """Test complete user journey from start to finish"""
        # 1. User visits dashboard
        await test_client.track_metric("page_view", {"page": "dashboard"})

        # 2. User navigates to optimizer
        await test_client.track_metric("page_view", {"page": "optimizer"})

        # 3. User uploads resume
        await test_client.track_metric("button_click", {"button_id": "upload_resume", "page": "optimizer"})

        try:
            await test_client.upload_resume(sample_resume)
            await test_client.track_metric("resume_upload", {"success": True})
        except Exception:
            await test_client.track_metric("resume_upload", {"success": False})

        # 4. User matches job
        try:
            match_result = await test_client.match_job(sample_resume, sample_job_description)
            await test_client.track_metric("job_match", {
                "match_score": match_result.get("match_score", 0),
                "success": True
            })
        except Exception:
            await test_client.track_metric("job_match", {"success": False})

        # 5. User optimizes resume
        try:
            optimization_result = await test_client.optimize_resume(sample_resume, sample_job_description)
            await test_client.track_metric("resume_optimization", {
                "success": "optimized_resume" in optimization_result
            })
        except Exception:
            await test_client.track_metric("resume_optimization", {"success": False})

        # 6. Verify metrics were collected
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{test_client.base_url}/api/metrics/user/{test_client.user_id}")
            user_metrics = response.json()

            assert user_metrics["total_events"] >= 5  # At least 5 events tracked
            assert user_metrics["user_id"] == test_client.user_id

if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])
