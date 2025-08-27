"""FastAPI entrypoint mounting modular AI router.

Legacy inlined AI endpoints have been removed; all AI functionality
is provided via `app/routers/ai_routes.py`. This file now only
handles app creation, basic health/meta endpoints, and OpenAI
availability detection for banner/logging.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from pydantic import BaseModel
from datetime import datetime
import os
import logging
import uvicorn

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("recruitly")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - replaces deprecated on_event"""
    # Startup
    logger.info("🚀 Recruitly AI API starting up...")
    initialize_ai_services()
    mount_routers()
    logger.info("✅ Startup complete")
    
    yield
    
    # Shutdown
    logger.info("🛑 Recruitly AI API shutting down...")
    logger.info("✅ Shutdown complete")

app = FastAPI(
    title="Recruitly AI API",
    version="1.3.0",
    description="AI-Powered Resume Optimization Platform (modular router)",
    lifespan=lifespan
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Global exception handler for better error responses
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_type": type(exc).__name__,
            "timestamp": datetime.now().isoformat()
        }
    )

# HTTP exception handler for validation errors
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with proper CORS headers"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Add explicit OPTIONS handler for CORS preflight
@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle CORS preflight requests"""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400"
        }
    )

# Initialize AI availability flags
ENHANCED_AI_AVAILABLE = False
OPENAI_AVAILABLE = False
_INITIALIZATION_DONE = False
openai_client = None

def initialize_ai_services():
    """Initialize AI services once to prevent duplicate initialization"""
    global ENHANCED_AI_AVAILABLE, OPENAI_AVAILABLE, _INITIALIZATION_DONE, openai_client

    if _INITIALIZATION_DONE:
        return

    # Check OpenAI configuration and import services
    if os.getenv("OPENAI_API_KEY"):
        try:
            import openai  # type: ignore
            # Initialize OpenAI client with explicit parameters only
            openai_client = openai.OpenAI(
                api_key=os.getenv("OPENAI_API_KEY")
            )
            OPENAI_AVAILABLE = True
            ENHANCED_AI_AVAILABLE = True
            print("✅ Enhanced AI pipeline initialized successfully!")
            print(f"🔍 OpenAI API Key: {'Configured' if os.getenv('OPENAI_API_KEY') else 'Not Set'}")
        except Exception as e:
            print(f"⚠️ OpenAI initialization failed: {e}")
            ENHANCED_AI_AVAILABLE = False
            OPENAI_AVAILABLE = False
    else:
        print("⚠️ No OpenAI API key found - using mock responses")

    _INITIALIZATION_DONE = True

############################
# Mock / Fallback Functions
############################
async def mock_analyze_job_match(resume_text: str, job_description: str):
    """Mock job matching analysis"""
    # Simple keyword matching for demo
    resume_lower = resume_text.lower()
    job_lower = job_description.lower()
    
    # Count matching keywords
    common_keywords = ['python', 'javascript', 'react', 'node', 'sql', 'git', 'api', 'database']
    matches = sum(1 for keyword in common_keywords if keyword in resume_lower and keyword in job_lower)
    
    overall_score = min(0.95, 0.4 + (matches * 0.08))  # Base score + keyword matches
    
    return {
        "match_scores": {
            "overall": round(overall_score, 2),
            "skills": round(min(0.95, overall_score + 0.05), 2),
            "experience": round(max(0.6, overall_score - 0.1), 2),
            "location": 0.9,
            "salary": 0.75
        },
        "recommendation": f"Strong match! Found {matches} relevant keywords." if matches > 3 else "Good potential - consider adding more relevant keywords.",
        "analysis_date": datetime.now().isoformat()
    }

async def mock_optimize_resume(resume_text: str, job_description: str):
    """Mock resume optimization"""
    # Simple enhancements
    enhanced_resume = resume_text
    
    # Replace weak words with stronger ones
    replacements = {
        "worked with": "architected and implemented",
        "helped": "collaborated to",
        "did": "executed",
        "made": "developed",
        "used": "leveraged",
        "built": "designed and developed"
    }
    
    improvements = []
    keywords_added = []
    
    for weak, strong in replacements.items():
        if weak in enhanced_resume.lower():
            enhanced_resume = enhanced_resume.replace(weak, strong)
            improvements.append(f"Replaced '{weak}' with '{strong}' for stronger impact")
    
    # Add relevant keywords from job description
    job_keywords = ['python', 'javascript', 'react', 'node.js', 'api', 'database', 'git', 'agile']
    for keyword in job_keywords:
        if keyword in job_description.lower() and keyword not in enhanced_resume.lower():
            enhanced_resume += f"\n• Proficient with {keyword}"
            keywords_added.append(keyword)
            improvements.append(f"Added relevant keyword: {keyword}")
    
    if not improvements:
        improvements = ["Enhanced professional language and formatting", "Optimized for ATS compatibility"]
    
    return {
        "optimized_resume": enhanced_resume,
        "improvements_made": improvements[:5],  # Limit to top 5
        "keywords_added": keywords_added[:5],
        "ats_score_improvement": "+28%",
        "match_score_prediction": 0.89,
        "optimization_summary": f"Enhanced resume with {len(improvements)} improvements and {len(keywords_added)} relevant keywords",
        "optimization_date": datetime.now().isoformat(),
        "_source": "mock"
    }

# Real OpenAI functions (if available)
async def real_optimize_resume(resume_text: str, job_description: str):
    """Real OpenAI resume optimization (with safe fallback & sanitization)"""
    global OPENAI_AVAILABLE
    if not OPENAI_AVAILABLE:
        return await mock_optimize_resume(resume_text, job_description)

    try:
        prompt = f"""You are an expert resume writer and ATS specialist. Optimize this resume for the specific job description.

RESUME TO OPTIMIZE:
{resume_text}

TARGET JOB:
{job_description}

REQUIREMENTS:
1. Keep all information truthful - never fabricate experience
2. Add relevant keywords naturally
3. Use strong action verbs
4. Make it ATS-friendly
5. Quantify achievements where possible

Return ONLY valid JSON:
{{
    "optimized_resume": "complete optimized resume text",
    "improvements_made": ["specific improvement 1", "specific improvement 2"],
    "keywords_added": ["keyword1", "keyword2"],
    "ats_score_improvement": "+X%",
    "optimization_summary": "brief summary of changes"
}}"""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2500
        )
        
        import json
        result = json.loads(response.choices[0].message.content.strip())
        result["optimization_date"] = datetime.now().isoformat()
        result["match_score_prediction"] = 0.91
        result["_source"] = "openai"
        return result
        
    except Exception as e:
        # Detect invalid / unauthorized key and disable further attempts
        msg = str(e)
        is_auth_error = any(token in msg.lower() for token in ["incorrect api key", "invalid_api_key", "401", "unauthorized"]) 
        if is_auth_error:
            OPENAI_AVAILABLE = False  # Prevent repeated failing calls
        # Sanitize potential leakage of key fragments
        sanitized = msg.split(".")[0] if "Incorrect API key" in msg else msg
        print(f"⚠️ OpenAI optimization failed -> falling back (sanitized): {sanitized}")
        fallback = await mock_optimize_resume(resume_text, job_description)
        fallback["_source"] = "mock_fallback"
        fallback["fallback_reason"] = "openai_error_auth" if is_auth_error else "openai_error_other"
        return fallback

# Request models
class JobMatchRequest(BaseModel):
    resume_text: str
    job_description: str

@app.get("/")
async def root():
    return {
        "message": "🚀 Recruitly AI API is running!", 
        "status": "healthy",
    "version": "1.3.0",
        "features": ["Resume Upload", "AI Optimization", "Job Matching"],
        "ai_status": "enhanced_ai" if ENHANCED_AI_AVAILABLE else "basic_ai" if bool(os.getenv("OPENAI_API_KEY")) else "demo_mode",
    "endpoints": ["/api/ai/upload-analyze-optimize", "/api/ai/optimize-resume", "/api/ai/batch-analyze-jobs", "/api/metrics/summary", "/health", "/docs"],
    "router_mounted": True,
    "legacy_endpoints_removed": True
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.3.0",
        "enhanced_ai_available": ENHANCED_AI_AVAILABLE,
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "mode": "enhanced_ai" if ENHANCED_AI_AVAILABLE else "basic_ai" if bool(os.getenv("OPENAI_API_KEY")) else "demo_mode"
    }


############################
# Mount Modular Routers
############################
def mount_routers():
    """Mount routers once to prevent duplicate mounting"""
    global _INITIALIZATION_DONE

    try:
        from app.routers import ai_routes as _ai_routes
        app.include_router(_ai_routes.router)
        logger.info("🔗 Mounted modular AI router /api/ai/*")
    except Exception as _r_err:
        logger.error(f"⚠️ Failed to mount modular AI router: {_r_err}")
        logger.error(f"   Error details: {type(_r_err).__name__}: {_r_err}")

    try:
        from app.routers import metrics_routes as _metrics_routes
        app.include_router(_metrics_routes.router)
        logger.info("🔗 Mounted metrics router /api/metrics/*")
    except Exception as _m_err:
        logger.error(f"⚠️ Failed to mount metrics router: {_m_err}")
        logger.error(f"   Error details: {type(_m_err).__name__}: {_m_err}")

# Only mount routers if running as main (not during import)
if __name__ == "__main__":
    mount_routers()

## Legacy inlined AI endpoints removed in favor of modular router (app/routers/ai_routes.py)

# Keep existing endpoints
@app.get("/api/dashboard")
async def get_dashboard():
    return {
        "total_applications": 47,
        "applications_this_month": 12,
        "pending_applications": 5,
        "interviews_scheduled": 3,
        "current_matches": 28,
        "auto_apply_enabled": True,
        "last_activity": "2025-08-23T15:30:00Z",
        "ai_features": {
            "resume_optimizations": 23,
            "semantic_matches": 28,
            "ats_improvements": "avg +31%",
            "mode": "real_ai" if OPENAI_AVAILABLE else "demo_mode"
        }
    }

@app.get("/api/matches")
async def get_matches():
    return {"matches": [], "total_matches": 0}

@app.get("/api/applications") 
async def get_applications():
    return {"applications": []}

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 RECRUITLY AI API STARTING")
    print("=" * 50)
    print("🌐 Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🔧 Input Validation: ENABLED")
    print("🛡️ Error Handling: ENHANCED")
    print("📊 Request Logging: ENABLED")
    print("=" * 50)

    # Configure uvicorn with enhanced logging
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,
        use_colors=True,
        reload_excludes=["*.pyc", "__pycache__", "*.log"],
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
                "access": {
                    "format": "%(asctime)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
                "access": {
                    "formatter": "access",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["default"], "level": "INFO"},
                "uvicorn.error": {"level": "INFO"},
                "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
            },
        }
    )