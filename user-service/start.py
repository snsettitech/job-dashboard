#!/usr/bin/env python3
"""
User Service Startup Script
Handles environment setup and service startup
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import psycopg2
        import pydantic
        print("✅ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def setup_environment():
    """Setup environment variables"""
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("📝 Creating .env file from template...")
            with open(env_example, 'r') as f:
                content = f.read()
            
            # Update with default values
            content = content.replace(
                "DATABASE_URL=postgresql://user:password@localhost:5432/user_service_db",
                "DATABASE_URL=postgresql://user_service_user:user_service_password@localhost:5432/user_service_db"
            )
            content = content.replace(
                "JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production",
                "JWT_SECRET_KEY=dev-secret-key-change-in-production"
            )
            
            with open(env_file, 'w') as f:
                f.write(content)
            print("✅ .env file created")
        else:
            print("⚠️  No env.example file found, creating basic .env...")
            basic_env = """# User Service Environment Configuration
ENVIRONMENT=development
DATABASE_URL=postgresql://user_service_user:user_service_password@localhost:5432/user_service_db
JWT_SECRET_KEY=dev-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
SESSION_TOKEN_EXPIRE_DAYS=30
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,http://localhost:8001
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_ECHO=false
"""
            with open(env_file, 'w') as f:
                f.write(basic_env)
            print("✅ Basic .env file created")
    else:
        print("✅ .env file already exists")

def check_database():
    """Check database connection"""
    try:
        from app.database import check_db_connection
        if check_db_connection():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            print("Make sure PostgreSQL is running and accessible")
            return False
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def start_service():
    """Start the user service"""
    print("🚀 Starting User Service...")
    
    try:
        # Start the service using uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", "0.0.0.0",
            "--port", "8001",
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Service stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Service failed to start: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def main():
    """Main startup function"""
    print("=" * 60)
    print("🚀 USER SERVICE STARTUP")
    print("=" * 60)
    
    # Check Python version
    check_python_version()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Check database (optional, will fail gracefully)
    print("\n🔍 Checking database connection...")
    db_ok = check_database()
    if not db_ok:
        print("⚠️  Database not available, but continuing...")
        print("   The service will fail to start if database is not accessible")
    
    print("\n" + "=" * 60)
    print("🌐 Service will be available at: http://localhost:8001")
    print("📚 API Documentation: http://localhost:8001/docs")
    print("❤️  Health Check: http://localhost:8001/health")
    print("=" * 60)
    
    # Start the service
    success = start_service()
    
    if not success:
        print("\n💥 Service startup failed!")
        print("Check the logs above for more details.")
        sys.exit(1)

if __name__ == "__main__":
    main()

