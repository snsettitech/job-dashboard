"""
User Service Microservice
FastAPI application for user management with JWT authentication and PostgreSQL
"""

import os
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("user-service")

# Global variables for startup/shutdown
startup_time = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global startup_time
    
    # Startup
    startup_time = time.time()
    logger.info("🚀 User Service starting up...")
    
    # Initialize database
    try:
        from app.database import init_db
        init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    # Clean up expired tokens
    try:
        from app.utils.auth import TokenManager
        from app.database import get_db_context
        with get_db_context() as db:
            TokenManager.cleanup_expired_tokens(db)
        logger.info("✅ Expired tokens cleaned up")
    except Exception as e:
        logger.warning(f"⚠️ Token cleanup failed: {e}")
    
    logger.info("✅ User Service startup complete")
    
    yield
    
    # Shutdown
    logger.info("🛑 User Service shutting down...")
    logger.info("✅ User Service shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="User Service API",
    version="1.0.0",
    description="User management microservice with JWT authentication and PostgreSQL",
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

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": f"HTTP_{exc.status_code}",
            "detail": exc.detail,
            "timestamp": time.time()
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error_code": "VALIDATION_ERROR",
            "detail": "Request validation failed",
            "errors": exc.errors(),
            "timestamp": time.time()
        }
    )

@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors"""
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error_code": "VALIDATION_ERROR",
            "detail": "Data validation failed",
            "errors": exc.errors(),
            "timestamp": time.time()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "INTERNAL_SERVER_ERROR",
            "detail": "Internal server error",
            "timestamp": time.time()
        }
    )

# Include routers
try:
    from app.routers import auth_routes, user_routes
    
    app.include_router(auth_routes.router, prefix="/api/v1")
    app.include_router(user_routes.router, prefix="/api/v1")
    
    logger.info("✅ Routers mounted successfully")
except Exception as e:
    logger.error(f"❌ Failed to mount routers: {e}")
    raise

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information"""
    uptime = time.time() - startup_time if startup_time else 0
    
    return {
        "message": "🚀 User Service API is running!",
        "service": "user-service",
        "version": "1.0.0",
        "status": "healthy",
        "uptime": round(uptime, 2),
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "auth": "/api/v1/auth",
            "users": "/api/v1/users"
        },
        "features": [
            "JWT Authentication",
            "User Registration & Login",
            "Profile Management",
            "Password Reset",
            "Email Verification",
            "Session Management",
            "Premium Subscriptions"
        ]
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        from app.database import check_db_connection, get_db_stats
        
        db_healthy = check_db_connection()
        db_stats = get_db_stats()
        
        uptime = time.time() - startup_time if startup_time else 0
        
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "service": "user-service",
            "version": "1.0.0",
            "uptime": round(uptime, 2),
            "database": {
                "status": "healthy" if db_healthy else "unhealthy",
                "stats": db_stats
            },
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "user-service",
            "version": "1.0.0",
            "error": str(e),
            "timestamp": time.time()
        }

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Get service metrics"""
    try:
        from app.database import get_db_context
        from app.models.user_models import User, UserSession, RefreshToken
        
        with get_db_context() as db:
            total_users = db.query(User).count()
            active_users = db.query(User).filter(User.is_active == True).count()
            premium_users = db.query(User).filter(User.is_premium == True).count()
            verified_users = db.query(User).filter(User.is_verified == True).count()
            active_sessions = db.query(UserSession).filter(
                UserSession.is_active == True,
                UserSession.expires_at > time.time()
            ).count()
            active_refresh_tokens = db.query(RefreshToken).filter(
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > time.time()
            ).count()
        
        uptime = time.time() - startup_time if startup_time else 0
        
        return {
            "metrics": {
                "total_users": total_users,
                "active_users": active_users,
                "premium_users": premium_users,
                "verified_users": verified_users,
                "active_sessions": active_sessions,
                "active_refresh_tokens": active_refresh_tokens
            },
            "uptime": round(uptime, 2),
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return {
            "error": str(e),
            "timestamp": time.time()
        }

# Database status endpoint
@app.get("/db/status")
async def database_status():
    """Get database status and statistics"""
    try:
        from app.database import check_db_connection, get_db_stats
        
        db_healthy = check_db_connection()
        db_stats = get_db_stats()
        
        return {
            "database": {
                "status": "healthy" if db_healthy else "unhealthy",
                "connection": db_healthy,
                "pool_stats": db_stats
            },
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Database status check failed: {e}")
        return {
            "database": {
                "status": "unhealthy",
                "error": str(e)
            },
            "timestamp": time.time()
        }

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🚀 USER SERVICE MICROSERVICE STARTING")
    print("=" * 60)
    print("🌐 Server: http://localhost:8001")
    print("📚 API Docs: http://localhost:8001/docs")
    print("📖 ReDoc: http://localhost:8001/redoc")
    print("❤️  Health: http://localhost:8001/health")
    print("📊 Metrics: http://localhost:8001/metrics")
    print("🗄️  DB Status: http://localhost:8001/db/status")
    print("=" * 60)
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
        access_log=True,
        use_colors=True
    )

