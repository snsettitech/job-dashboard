# ai-service/main.py - AI Service Main Application
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
from datetime import datetime

from app.routers.ai_routes import router as ai_router
from app.routers.pinecone_routes import router as pinecone_router
from app.database import init_db, check_db_health
from app.services.ai_service import ai_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ai_service.log")
    ]
)

logger = logging.getLogger(__name__)

# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting AI Service...")
    
    # Initialize database
    try:
        db_initialized = await init_db()
        if db_initialized:
            logger.info("✅ Database initialized successfully")
        else:
            logger.error("❌ Database initialization failed")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")
    
    # Test AI service connectivity
    try:
        test_embeddings = await ai_service.get_embeddings(["test"])
        if test_embeddings:
            logger.info("✅ AI service connectivity verified")
        else:
            logger.warning("⚠️ AI service connectivity issues detected")
    except Exception as e:
        logger.error(f"❌ AI service connectivity error: {e}")
    
    logger.info("🎉 AI Service startup completed")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down AI Service...")

# Create FastAPI application
app = FastAPI(
    title="AI Service",
    description="Enhanced AI-powered resume analysis and optimization service with OpenAI integration and vector embeddings",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Frontend development
        "http://localhost:8000",  # Main backend
        "http://localhost:8001",  # User service
        "http://localhost:8002",  # Resume service
        "http://localhost:8003",  # AI service
        "*"  # Allow all origins in development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "error_type": "UNHANDLED_EXCEPTION",
            "details": {
                "error": str(exc),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

# Include routers
app.include_router(ai_router)
app.include_router(pinecone_router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Service",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "description": "Enhanced AI-powered resume analysis and optimization service",
        "features": [
            "Semantic job-resume matching with vector embeddings",
            "AI-powered resume optimization",
            "Enhanced 3-stage optimization pipeline",
            "Batch job analysis",
            "Session management and tracking",
            "Quality validation and confidence scoring"
        ],
        "endpoints": {
            "api_docs": "/docs",
            "health_check": "/api/ai/health",
            "metrics": "/api/ai/metrics",
            "models": "/api/ai/models"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Basic health check"""
    try:
        # Check database health
        db_health = await check_db_health()
        
        # Check AI service
        try:
            test_embeddings = await ai_service.get_embeddings(["health check"])
            ai_status = "operational" if test_embeddings else "degraded"
        except Exception as e:
            ai_status = "down"
            logger.error(f"AI service health check failed: {e}")
        
        overall_status = "healthy" if db_health["status"] == "healthy" and ai_status == "operational" else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": db_health["status"],
                "ai_service": ai_status,
                "api": "operational"
            },
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "version": "1.0.0"
        }

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint"""
    try:
        from app.database import get_db_stats
        db_stats = await get_db_stats()
        
        return {
            "service": "AI Service",
            "timestamp": datetime.utcnow().isoformat(),
            "database_stats": db_stats,
            "ai_service": {
                "embedding_model": ai_service.embedding_model,
                "chat_model": ai_service.chat_model,
                "status": "operational"
            }
        }
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return {
            "service": "AI Service",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

# API info endpoint
@app.get("/api/info")
async def api_info():
    """API information endpoint"""
    return {
        "service": "AI Service",
        "version": "1.0.0",
        "description": "Enhanced AI-powered resume analysis and optimization service",
        "endpoints": {
            "job_matching": {
                "url": "/api/ai/analyze-match",
                "method": "POST",
                "description": "Analyze semantic match between resume and job description"
            },
            "resume_optimization": {
                "url": "/api/ai/optimize-resume",
                "method": "POST",
                "description": "AI-powered resume optimization for specific job"
            },
            "enhanced_optimization": {
                "url": "/api/ai/enhanced-optimization",
                "method": "POST",
                "description": "Enhanced 3-stage AI optimization pipeline"
            },
            "batch_analysis": {
                "url": "/api/ai/batch-analyze",
                "method": "POST",
                "description": "Analyze resume match against multiple job descriptions"
            },
            "embeddings": {
                "url": "/api/ai/embeddings",
                "method": "POST",
                "description": "Generate vector embeddings for text content"
            },
            "session_status": {
                "url": "/api/ai/session/{session_id}/status",
                "method": "GET",
                "description": "Get processing session status and progress"
            },
            "user_sessions": {
                "url": "/api/ai/sessions",
                "method": "GET",
                "description": "List processing sessions for a user"
            },
            "health_check": {
                "url": "/api/ai/health",
                "method": "GET",
                "description": "Check AI service health and connectivity"
            },
            "usage_metrics": {
                "url": "/api/ai/metrics",
                "method": "GET",
                "description": "Get AI service usage metrics and analytics"
            },
            "available_models": {
                "url": "/api/ai/models",
                "method": "GET",
                "description": "List available AI models and their capabilities"
            }
        },
        "features": [
            "Semantic job-resume matching with OpenAI embeddings",
            "AI-powered resume optimization with GPT models",
            "Enhanced 3-stage optimization pipeline",
            "Batch job analysis with parallel processing",
            "Vector embeddings generation and storage",
            "Session management and progress tracking",
            "Quality validation and confidence scoring",
            "Comprehensive error handling and fallbacks",
            "Database persistence for all operations",
            "Health monitoring and metrics collection"
        ],
        "models": {
            "embedding_models": ["text-embedding-3-small", "text-embedding-3-large"],
            "chat_models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
            "default_embedding": ai_service.embedding_model,
            "default_chat": ai_service.chat_model
        },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_spec": "/openapi.json"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("AI_SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("AI_SERVICE_PORT", "8003"))
    reload = os.getenv("AI_SERVICE_RELOAD", "false").lower() == "true"
    
    logger.info(f"Starting AI Service on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
