# backend/main.py - FastAPI Server for Recruitly
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Recruitly API", version="1.0.0")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Recruitly API is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/api/dashboard")
async def get_dashboard():
    return {
        "total_applications": 47,
        "applications_this_month": 12,
        "pending_applications": 5,
        "interviews_scheduled": 3,
        "current_matches": 28,
        "auto_apply_enabled": True,
        "last_activity": "2025-08-23T15:30:00Z"
    }

@app.get("/api/matches")
async def get_matches():
    return {
        "matches": [
            {
                "match_id": "1",
                "job": {
                    "id": "1",
                    "title": "Senior AI Engineer",
                    "company": "OpenAI",
                    "location": "San Francisco, CA (Remote)",
                    "posted_date": "2025-08-20T00:00:00Z",
                    "salary_range": [180000, 250000],
                    "required_skills": ["Python", "PyTorch", "Machine Learning", "LLMs"],
                    "quality_score": 0.95,
                    "source_url": "https://openai.com/careers/senior-ai-engineer"
                },
                "scores": {
                    "overall": 0.94,
                    "skills": 0.98,
                    "experience": 0.92,
                    "location": 1.0,
                    "salary": 0.85
                },
                "rank": 1,
                "already_applied": False
            },
            {
                "match_id": "2",
                "job": {
                    "id": "2",
                    "title": "Full Stack Developer - AI Platform",
                    "company": "Anthropic",
                    "location": "Remote",
                    "posted_date": "2025-08-21T00:00:00Z",
                    "salary_range": [150000, 200000],
                    "required_skills": ["React", "Python", "FastAPI", "PostgreSQL"],
                    "quality_score": 0.91,
                    "source_url": "https://anthropic.com/careers/fullstack"
                },
                "scores": {
                    "overall": 0.88,
                    "skills": 0.95,
                    "experience": 0.85,
                    "location": 1.0,
                    "salary": 0.78
                },
                "rank": 2,
                "already_applied": False
            },
            {
                "match_id": "3",
                "job": {
                    "id": "3",
                    "title": "Principal Software Engineer",
                    "company": "Microsoft",
                    "location": "Seattle, WA (Hybrid)",
                    "posted_date": "2025-08-19T00:00:00Z",
                    "salary_range": [200000, 300000],
                    "required_skills": ["C#", "Azure", "Distributed Systems", "Leadership"],
                    "quality_score": 0.87,
                    "source_url": "https://microsoft.com/careers/principal-swe"
                },
                "scores": {
                    "overall": 0.84,
                    "skills": 0.88,
                    "experience": 0.95,
                    "location": 0.70,
                    "salary": 0.92
                },
                "rank": 3,
                "already_applied": False
            },
            {
                "match_id": "4",
                "job": {
                    "id": "4",
                    "title": "Senior Backend Engineer",
                    "company": "Stripe",
                    "location": "New York, NY (Remote OK)",
                    "posted_date": "2025-08-22T00:00:00Z",
                    "salary_range": [160000, 220000],
                    "required_skills": ["Go", "Kubernetes", "PostgreSQL", "Payment Systems"],
                    "quality_score": 0.83,
                    "source_url": "https://stripe.com/jobs/backend-engineer"
                },
                "scores": {
                    "overall": 0.81,
                    "skills": 0.85,
                    "experience": 0.88,
                    "location": 0.85,
                    "salary": 0.82
                },
                "rank": 4,
                "already_applied": False
            },
            {
                "match_id": "5",
                "job": {
                    "id": "5",
                    "title": "DevOps Engineer - AI Infrastructure",
                    "company": "Hugging Face",
                    "location": "Remote",
                    "posted_date": "2025-08-18T00:00:00Z",
                    "salary_range": [140000, 180000],
                    "required_skills": ["AWS", "Docker", "Kubernetes", "Python", "MLOps"],
                    "quality_score": 0.80,
                    "source_url": "https://huggingface.co/jobs/devops"
                },
                "scores": {
                    "overall": 0.78,
                    "skills": 0.82,
                    "experience": 0.75,
                    "location": 1.0,
                    "salary": 0.75
                },
                "rank": 5,
                "already_applied": False
            }
        ],
        "total_matches": 28
    }

@app.get("/api/applications")
async def get_applications():
    return {
        "applications": [
            {
                "id": "1",
                "job": {
                    "title": "Senior ML Engineer",
                    "company": "Google DeepMind",
                    "location": "London, UK"
                },
                "status": "interview_scheduled",
                "application_method": "automated",
                "submitted_at": "2025-08-15T14:30:00Z",
                "last_status_update": "2025-08-20T09:15:00Z",
                "needs_follow_up": False,
                "follow_up_sent": False
            },
            {
                "id": "2",
                "job": {
                    "title": "Staff Software Engineer",
                    "company": "Tesla",
                    "location": "Austin, TX"
                },
                "status": "submitted",
                "application_method": "automated",
                "submitted_at": "2025-08-18T11:20:00Z",
                "last_status_update": "2025-08-18T11:20:00Z",
                "needs_follow_up": True,
                "follow_up_sent": False
            },
            {
                "id": "3",
                "job": {
                    "title": "Principal Engineer - AI",
                    "company": "Meta",
                    "location": "Menlo Park, CA"
                },
                "status": "pending",
                "application_method": "automated",
                "submitted_at": "2025-08-21T16:45:00Z",
                "last_status_update": "2025-08-21T16:45:00Z",
                "needs_follow_up": False,
                "follow_up_sent": False
            },
            {
                "id": "4",
                "job": {
                    "title": "Senior Python Developer",
                    "company": "Spotify",
                    "location": "Stockholm, Sweden"
                },
                "status": "rejected",
                "application_method": "automated",
                "submitted_at": "2025-08-10T10:30:00Z",
                "last_status_update": "2025-08-17T14:22:00Z",
                "needs_follow_up": False,
                "follow_up_sent": True
            },
            {
                "id": "5",
                "job": {
                    "title": "Lead Software Architect",
                    "company": "Netflix",
                    "location": "Los Gatos, CA"
                },
                "status": "offer",
                "application_method": "automated",
                "submitted_at": "2025-08-05T09:15:00Z",
                "last_status_update": "2025-08-22T11:30:00Z",
                "needs_follow_up": False,
                "follow_up_sent": False
            }
        ]
    }

@app.post("/api/jobs/{job_id}/apply")
async def apply_to_job(job_id: str):
    return {
        "message": "🚀 Application submitted successfully!", 
        "task_id": f"task_{job_id}",
        "status": "processing",
        "estimated_completion": "2-5 minutes"
    }

# Health endpoint for monitoring
@app.get("/api/status")
async def get_status():
    return {
        "api_status": "healthy",
        "database_status": "connected",
        "ai_service_status": "ready",
        "last_updated": "2025-08-23T15:30:00Z",
        "version": "1.0.0-mvp"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Recruitly API Server...")
    print("📊 Dashboard: http://localhost:8000")
    print("🔗 API Docs: http://localhost:8000/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)