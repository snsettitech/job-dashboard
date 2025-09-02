# ai-service/app/database.py - AI Service Database Configuration
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Optional, Dict, Any
import os
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://ai_user:ai_password@localhost:5434/ai_service_db"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    echo=os.getenv("DB_ECHO", "false").lower() == "true"
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

async def init_db():
    """Initialize database tables"""
    try:
        # Import all models to ensure they are registered
        from .models.ai_models import (
            AIProcessingSession, Embedding, ResumeOptimization, 
            JobMatchAnalysis, VectorIndex, AIUsageMetrics, AIServiceConfig
        )
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Initialize default configuration
        await init_default_config()
        
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

async def init_default_config():
    """Initialize default AI service configuration"""
    try:
        with get_db_context() as db:
            # Check if config already exists
            existing_config = db.query(AIServiceConfig).filter(
                AIServiceConfig.config_key == "default_embedding_model"
            ).first()
            
            if not existing_config:
                # Insert default configuration
                default_configs = [
                    {
                        "config_key": "default_embedding_model",
                        "config_value": "text-embedding-3-small",
                        "config_type": "string",
                        "description": "Default embedding model for vector generation"
                    },
                    {
                        "config_key": "default_chat_model",
                        "config_value": "gpt-4o-mini",
                        "config_type": "string",
                        "description": "Default chat model for AI processing"
                    },
                    {
                        "config_key": "max_retries",
                        "config_value": "3",
                        "config_type": "int",
                        "description": "Maximum retry attempts for AI calls"
                    },
                    {
                        "config_key": "confidence_threshold",
                        "config_value": "70.0",
                        "config_type": "float",
                        "description": "Minimum confidence threshold for results"
                    },
                    {
                        "config_key": "max_tokens_per_request",
                        "config_value": "4000",
                        "config_type": "int",
                        "description": "Maximum tokens per AI request"
                    },
                    {
                        "config_key": "enable_enhanced_optimization",
                        "config_value": "true",
                        "config_type": "bool",
                        "description": "Enable enhanced optimization pipeline"
                    },
                    {
                        "config_key": "vector_store_type",
                        "config_value": "postgresql",
                        "config_type": "string",
                        "description": "Vector store type (postgresql, chroma, faiss)"
                    }
                ]
                
                for config in default_configs:
                    db_config = AIServiceConfig(**config)
                    db.add(db_config)
                
                db.commit()
                logger.info("Default configuration initialized successfully")
                
    except Exception as e:
        logger.error(f"Default configuration initialization failed: {e}")

async def check_db_health() -> Dict[str, Any]:
    """Check database health and connectivity"""
    try:
        with get_db_context() as db:
            # Test basic connectivity
            result = db.execute(text("SELECT 1"))
            result.fetchone()
            
            # Check table counts
            session_count = db.query(AIProcessingSession).count()
            embedding_count = db.query(Embedding).count()
            optimization_count = db.query(ResumeOptimization).count()
            analysis_count = db.query(JobMatchAnalysis).count()
            
            return {
                "status": "healthy",
                "connection": "ok",
                "tables": {
                    "ai_processing_sessions": session_count,
                    "embeddings": embedding_count,
                    "resume_optimizations": optimization_count,
                    "job_match_analyses": analysis_count
                },
                "database_url": DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else "local"
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "connection": "failed",
            "error": str(e),
            "database_url": DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else "local"
        }

async def get_db_stats() -> Dict[str, Any]:
    """Get database statistics"""
    try:
        with get_db_context() as db:
            stats = {
                "total_sessions": db.query(AIProcessingSession).count(),
                "completed_sessions": db.query(AIProcessingSession).filter(
                    AIProcessingSession.status == "completed"
                ).count(),
                "failed_sessions": db.query(AIProcessingSession).filter(
                    AIProcessingSession.status == "failed"
                ).count(),
                "total_embeddings": db.query(Embedding).count(),
                "total_optimizations": db.query(ResumeOptimization).count(),
                "total_analyses": db.query(JobMatchAnalysis).count(),
                "high_confidence_results": db.query(ResumeOptimization).filter(
                    ResumeOptimization.confidence_score >= 80.0
                ).count()
            }
            
            # Get recent activity (last 24 hours)
            from datetime import datetime, timedelta
            yesterday = datetime.utcnow() - timedelta(days=1)
            
            recent_stats = {
                "recent_sessions": db.query(AIProcessingSession).filter(
                    AIProcessingSession.created_at >= yesterday
                ).count(),
                "recent_optimizations": db.query(ResumeOptimization).filter(
                    ResumeOptimization.created_at >= yesterday
                ).count(),
                "recent_analyses": db.query(JobMatchAnalysis).filter(
                    JobMatchAnalysis.created_at >= yesterday
                ).count()
            }
            
            stats.update(recent_stats)
            return stats
            
    except Exception as e:
        logger.error(f"Database stats collection failed: {e}")
        return {"error": str(e)}

async def cleanup_old_sessions(days_to_keep: int = 30):
    """Clean up old processing sessions"""
    try:
        from datetime import datetime, timedelta
        from .models.ai_models import AIProcessingSession, Embedding, ResumeOptimization, JobMatchAnalysis
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        with get_db_context() as db:
            # Delete old sessions and related data
            old_sessions = db.query(AIProcessingSession).filter(
                AIProcessingSession.created_at < cutoff_date
            ).all()
            
            deleted_count = 0
            for session in old_sessions:
                # Delete related data first
                db.query(Embedding).filter(Embedding.session_id == session.id).delete()
                db.query(ResumeOptimization).filter(ResumeOptimization.session_id == session.id).delete()
                db.query(JobMatchAnalysis).filter(JobMatchAnalysis.session_id == session.id).delete()
                
                # Delete session
                db.delete(session)
                deleted_count += 1
            
            db.commit()
            logger.info(f"Cleaned up {deleted_count} old sessions")
            return deleted_count
            
    except Exception as e:
        logger.error(f"Session cleanup failed: {e}")
        return 0

async def backup_database(backup_path: str):
    """Create database backup"""
    try:
        import subprocess
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_path}/ai_service_backup_{timestamp}.sql"
        
        # Extract database connection details
        if DATABASE_URL.startswith("postgresql://"):
            # Parse connection string
            parts = DATABASE_URL.replace("postgresql://", "").split("@")
            if len(parts) == 2:
                auth, host_db = parts
                username, password = auth.split(":")
                host_port, database = host_db.split("/")
                host, port = host_port.split(":")
                
                # Create backup using pg_dump
                cmd = [
                    "pg_dump",
                    f"--host={host}",
                    f"--port={port}",
                    f"--username={username}",
                    f"--dbname={database}",
                    "--no-password",
                    f"--file={backup_file}"
                ]
                
                # Set password environment variable
                env = os.environ.copy()
                env["PGPASSWORD"] = password
                
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"Database backup created: {backup_file}")
                    return backup_file
                else:
                    logger.error(f"Database backup failed: {result.stderr}")
                    return None
                    
        return None
        
    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        return None

async def restore_database(backup_file: str):
    """Restore database from backup"""
    try:
        import subprocess
        
        # Extract database connection details
        if DATABASE_URL.startswith("postgresql://"):
            parts = DATABASE_URL.replace("postgresql://", "").split("@")
            if len(parts) == 2:
                auth, host_db = parts
                username, password = auth.split(":")
                host_port, database = host_db.split("/")
                host, port = host_port.split(":")
                
                # Restore using psql
                cmd = [
                    "psql",
                    f"--host={host}",
                    f"--port={port}",
                    f"--username={username}",
                    f"--dbname={database}",
                    "--no-password",
                    f"--file={backup_file}"
                ]
                
                env = os.environ.copy()
                env["PGPASSWORD"] = password
                
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"Database restored from: {backup_file}")
                    return True
                else:
                    logger.error(f"Database restore failed: {result.stderr}")
                    return False
                    
        return False
        
    except Exception as e:
        logger.error(f"Database restore failed: {e}")
        return False

# Utility functions for database operations
def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Drop all database tables"""
    Base.metadata.drop_all(bind=engine)

def reset_database():
    """Reset database by dropping and recreating all tables"""
    drop_tables()
    create_tables()
    logger.info("Database reset completed")



