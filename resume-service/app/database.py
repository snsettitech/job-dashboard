# resume-service/app/database.py
import os
from sqlalchemy import create_engine, Column, String, Text, Integer, Boolean, DateTime, Float, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/resume_service_db"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv("DB_ECHO", "false").lower() == "true"
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_context() -> Session:
    """Get database session for context managers"""
    return SessionLocal()

def init_db():
    """Initialize database tables"""
    try:
        # Import all models to ensure they are registered
        from .models.resume_models import Resume, ResumeVersion, ResumeOptimization, ResumeAnalysis, StorageConfig
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def check_db_connection() -> bool:
    """Check database connection"""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def get_db_stats() -> dict:
    """Get database statistics"""
    try:
        with engine.connect() as connection:
            # Get table counts
            tables = ['resumes', 'resume_versions', 'resume_optimizations', 'resume_analyses', 'storage_configs']
            stats = {}
            
            for table in tables:
                result = connection.execute(f"SELECT COUNT(*) FROM {table}")
                count = result.scalar()
                stats[f"{table}_count"] = count
            
            # Get database size
            result = connection.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as db_size
            """)
            stats['database_size'] = result.scalar()
            
            return stats
            
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {"error": str(e)}

class DatabaseManager:
    """Database management utilities"""
    
    @staticmethod
    def create_tables():
        """Create all database tables"""
        init_db()
    
    @staticmethod
    def drop_tables():
        """Drop all database tables"""
        try:
            Base.metadata.drop_all(bind=engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    @staticmethod
    def reset_database():
        """Reset database (drop and recreate tables)"""
        try:
            DatabaseManager.drop_tables()
            DatabaseManager.create_tables()
            logger.info("Database reset successfully")
        except Exception as e:
            logger.error(f"Failed to reset database: {e}")
            raise
    
    @staticmethod
    def backup_database(backup_path: str):
        """Create database backup"""
        try:
            import subprocess
            
            # Extract database connection info from URL
            from urllib.parse import urlparse
            parsed = urlparse(DATABASE_URL)
            
            # Create backup command
            backup_cmd = [
                'pg_dump',
                f'--host={parsed.hostname}',
                f'--port={parsed.port or 5432}',
                f'--username={parsed.username}',
                f'--dbname={parsed.path[1:]}',  # Remove leading slash
                f'--file={backup_path}'
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            if parsed.password:
                env['PGPASSWORD'] = parsed.password
            
            # Execute backup
            subprocess.run(backup_cmd, env=env, check=True)
            logger.info(f"Database backup created: {backup_path}")
            
        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            raise
    
    @staticmethod
    def restore_database(backup_path: str):
        """Restore database from backup"""
        try:
            import subprocess
            
            # Extract database connection info from URL
            from urllib.parse import urlparse
            parsed = urlparse(DATABASE_URL)
            
            # Create restore command
            restore_cmd = [
                'psql',
                f'--host={parsed.hostname}',
                f'--port={parsed.port or 5432}',
                f'--username={parsed.username}',
                f'--dbname={parsed.path[1:]}',  # Remove leading slash
                f'--file={backup_path}'
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            if parsed.password:
                env['PGPASSWORD'] = parsed.password
            
            # Execute restore
            subprocess.run(restore_cmd, env=env, check=True)
            logger.info(f"Database restored from: {backup_path}")
            
        except Exception as e:
            logger.error(f"Failed to restore database: {e}")
            raise

class DatabaseConfig:
    """Database configuration management"""
    
    @staticmethod
    def get_connection_string() -> str:
        """Get database connection string"""
        return DATABASE_URL
    
    @staticmethod
    def get_pool_config() -> dict:
        """Get connection pool configuration"""
        return {
            "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
            "pool_pre_ping": True,
            "pool_recycle": 3600
        }
    
    @staticmethod
    def is_development() -> bool:
        """Check if running in development mode"""
        return os.getenv("ENVIRONMENT", "development").lower() == "development"
    
    @staticmethod
    def is_production() -> bool:
        """Check if running in production mode"""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    @staticmethod
    def get_logging_config() -> dict:
        """Get database logging configuration"""
        return {
            "echo": os.getenv("DB_ECHO", "false").lower() == "true",
            "echo_pool": os.getenv("DB_ECHO_POOL", "false").lower() == "true"
        }

# Health check function
def health_check() -> dict:
    """Perform database health check"""
    try:
        # Test connection
        connection_ok = check_db_connection()
        
        if not connection_ok:
            return {
                "status": "unhealthy",
                "database": "connection_failed",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Get basic stats
        stats = get_db_stats()
        
        return {
            "status": "healthy",
            "database": "connected",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

