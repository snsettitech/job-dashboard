# resume-service/main.py
import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.database import init_db, health_check as db_health_check
from app.services.storage_service import StorageService
from app.routers import resume_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Service startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Resume Service...")
    
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized successfully")
        
        # Initialize storage service
        storage_provider = os.getenv("STORAGE_PROVIDER", "s3")
        storage_service = StorageService(provider=storage_provider)
        await storage_service.health_check()
        logger.info(f"Storage service ({storage_provider}) initialized successfully")
        
        logger.info("Resume Service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start Resume Service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Resume Service...")

# Create FastAPI app
app = FastAPI(
    title="Resume Service API",
    version="1.0.0",
    description="Resume management microservice with S3/Railway storage integration",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(resume_routes.router, prefix="/api/v1")

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Validation error",
            "errors": exc.errors(),
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path
        }
    )

@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors"""
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Data validation error",
            "errors": exc.errors(),
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path
        }
    )

# Health check endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Resume Service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "api": "/api/v1"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database health
        db_status = db_health_check()
        
        # Check storage health
        storage_provider = os.getenv("STORAGE_PROVIDER", "s3")
        storage_service = StorageService(provider=storage_provider)
        storage_status = await storage_service.health_check()
        
        # Determine overall status
        overall_status = "healthy"
        if db_status.get("status") != "healthy" or storage_status.get("status") != "healthy":
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": db_status,
                "storage": storage_status
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

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with service information"""
    try:
        # Database health
        db_status = db_health_check()
        
        # Storage health
        storage_provider = os.getenv("STORAGE_PROVIDER", "s3")
        storage_service = StorageService(provider=storage_provider)
        storage_status = await storage_service.health_check()
        
        # Environment info
        env_info = {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "storage_provider": storage_provider,
            "database_url": os.getenv("DATABASE_URL", "not_set")[:20] + "..." if os.getenv("DATABASE_URL") else "not_set"
        }
        
        return {
            "status": "healthy" if db_status.get("status") == "healthy" and storage_status.get("status") == "healthy" else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": env_info,
            "services": {
                "database": db_status,
                "storage": storage_status
            }
        }
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "version": "1.0.0"
        }

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Get service metrics"""
    try:
        from app.database import get_db_stats
        
        # Get database stats
        db_stats = get_db_stats()
        
        # Get storage info
        storage_provider = os.getenv("STORAGE_PROVIDER", "s3")
        storage_service = StorageService(provider=storage_provider)
        
        # Get file count from storage
        files = await storage_service.list_files(prefix="resumes/", max_keys=1000)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_stats,
            "storage": {
                "provider": storage_provider,
                "files_count": len(files),
                "total_size": sum(f.get("size", 0) for f in files)
            },
            "service": {
                "version": "1.0.0",
                "uptime": "running"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

# API info endpoint
@app.get("/api/info")
async def api_info():
    """Get API information"""
    return {
        "name": "Resume Service API",
        "version": "1.0.0",
        "description": "Resume management microservice with cloud storage integration",
        "features": [
            "Resume upload and storage",
            "File processing and text extraction",
            "Resume optimization",
            "Resume analysis",
            "Version control",
            "Cloud storage integration (S3/Railway)"
        ],
        "endpoints": {
            "resumes": "/api/v1/resumes",
            "upload": "/api/v1/resumes/upload",
            "optimization": "/api/v1/resumes/{id}/optimize",
            "analysis": "/api/v1/resumes/{id}/analyze",
            "versions": "/api/v1/resumes/{id}/versions",
            "download": "/api/v1/resumes/{id}/download"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }

# Development endpoints (only in development mode)
if os.getenv("ENVIRONMENT", "development").lower() == "development":
    
    @app.get("/dev/db/stats")
    async def dev_db_stats():
        """Development endpoint to get database statistics"""
        try:
            from app.database import get_db_stats
            return get_db_stats()
        except Exception as e:
            return {"error": str(e)}
    
    @app.get("/dev/storage/files")
    async def dev_storage_files():
        """Development endpoint to list storage files"""
        try:
            storage_provider = os.getenv("STORAGE_PROVIDER", "s3")
            storage_service = StorageService(provider=storage_provider)
            files = await storage_service.list_files(prefix="", max_keys=100)
            return {"files": files, "count": len(files)}
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8002"))
    reload = os.getenv("ENVIRONMENT", "development").lower() == "development"
    
    logger.info(f"Starting Resume Service on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True,
        use_colors=True
    )



