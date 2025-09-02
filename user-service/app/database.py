"""
Database Configuration and Session Management
PostgreSQL connection and session handling for user service
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/user_service_db"
)

# Database engine configuration
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections every hour
    echo=os.getenv("DB_ECHO", "false").lower() == "true"
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
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
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    try:
        # Import all models to ensure they are registered
        from .models.user_models import (
            User, UserProfile, UserPreference, UserSession,
            RefreshToken, PasswordReset, EmailVerification
        )
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def check_db_connection():
    """Check database connection health"""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False

def get_db_stats():
    """Get database statistics"""
    try:
        with engine.connect() as connection:
            # Get connection pool stats
            pool = engine.pool
            stats = {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
            return stats
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return None

class DatabaseManager:
    """Database management utilities"""
    
    @staticmethod
    def create_tables():
        """Create all database tables"""
        init_db()
    
    @staticmethod
    def drop_tables():
        """Drop all database tables (use with caution)"""
        try:
            Base.metadata.drop_all(bind=engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    @staticmethod
    def reset_database():
        """Reset database (drop and recreate all tables)"""
        try:
            DatabaseManager.drop_tables()
            DatabaseManager.create_tables()
            logger.info("Database reset successfully")
        except Exception as e:
            logger.error(f"Failed to reset database: {e}")
            raise
    
    @staticmethod
    def health_check():
        """Perform database health check"""
        return {
            "status": "healthy" if check_db_connection() else "unhealthy",
            "connection": check_db_connection(),
            "pool_stats": get_db_stats()
        }

# Database migration utilities (for Alembic)
def get_alembic_config():
    """Get Alembic configuration"""
    return {
        "script_location": "alembic",
        "sqlalchemy.url": DATABASE_URL,
        "file_template": "%%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s"
    }

# Environment-specific configurations
class DatabaseConfig:
    """Database configuration based on environment"""
    
    @staticmethod
    def get_database_url():
        """Get database URL based on environment"""
        env = os.getenv("ENVIRONMENT", "development")
        
        if env == "production":
            return os.getenv("DATABASE_URL")
        elif env == "testing":
            return os.getenv("TEST_DATABASE_URL", "postgresql://test:test@localhost:5432/user_service_test")
        else:
            return os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/user_service_dev")
    
    @staticmethod
    def get_pool_config():
        """Get connection pool configuration based on environment"""
        env = os.getenv("ENVIRONMENT", "development")
        
        if env == "production":
            return {
                "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
                "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "30")),
                "pool_recycle": 3600
            }
        elif env == "testing":
            return {
                "pool_size": 5,
                "max_overflow": 10,
                "pool_recycle": 300
            }
        else:
            return {
                "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
                "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
                "pool_recycle": 3600
            }

