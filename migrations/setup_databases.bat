@echo off
setlocal enabledelayedexpansion

REM PostgreSQL Database Setup Script for Job Dashboard (Windows)
REM This script creates the databases and runs all migrations for the microservices

REM Configuration
set "DB_HOST=%DB_HOST%"
if "%DB_HOST%"=="" set "DB_HOST=localhost"

set "DB_PORT=%DB_PORT%"
if "%DB_PORT%"=="" set "DB_PORT=5432"

set "DB_USER=%DB_USER%"
if "%DB_USER%"=="" set "DB_USER=postgres"

set "DB_PASSWORD=%DB_PASSWORD%"
if "%DB_PASSWORD%"=="" set "DB_PASSWORD="

REM Database names
set "USER_DB=user_service_db"
set "RESUME_DB=resume_service_db"
set "AI_DB=ai_service_db"

REM Flags
set "SETUP_USER=true"
set "SETUP_RESUME=true"
set "SETUP_AI=true"
set "VERIFY_ONLY=false"

REM Parse command line arguments
:parse_args
if "%1"=="" goto :main
if "%1"=="--user-only" (
    set "SETUP_USER=true"
    set "SETUP_RESUME=false"
    set "SETUP_AI=false"
    shift
    goto :parse_args
)
if "%1"=="--resume-only" (
    set "SETUP_USER=false"
    set "SETUP_RESUME=true"
    set "SETUP_AI=false"
    shift
    goto :parse_args
)
if "%1"=="--ai-only" (
    set "SETUP_USER=false"
    set "SETUP_RESUME=false"
    set "SETUP_AI=true"
    shift
    goto :parse_args
)
if "%1"=="--verify-only" (
    set "VERIFY_ONLY=true"
    shift
    goto :parse_args
)
if "%1"=="--help" (
    call :show_usage
    exit /b 0
)
shift
goto :parse_args

:main
echo ==========================================
echo   Job Dashboard Database Setup Script
echo ==========================================
echo.

REM Check if psql is available
where psql >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] psql command not found. Please install PostgreSQL client tools.
    exit /b 1
)

REM Check PostgreSQL connection
call :check_postgres
if %errorlevel% neq 0 (
    exit /b 1
)

if "%VERIFY_ONLY%"=="true" (
    call :verify_setup
    exit /b 0
)

REM Create databases
if "%SETUP_USER%"=="true" (
    call :create_database "%USER_DB%"
)

if "%SETUP_RESUME%"=="true" (
    call :create_database "%RESUME_DB%"
)

if "%SETUP_AI%"=="true" (
    call :create_database "%AI_DB%"
)

REM Run migrations
if "%SETUP_USER%"=="true" (
    call :run_migrations "User Service" "%USER_DB%" "user-service"
)

if "%SETUP_RESUME%"=="true" (
    call :run_migrations "Resume Service" "%RESUME_DB%" "resume-service"
)

if "%SETUP_AI%"=="true" (
    call :run_migrations "AI Service" "%AI_DB%" "ai-service"
)

REM Verify setup
call :verify_setup

echo.
echo ==========================================
echo [SUCCESS] Database setup completed successfully!
echo ==========================================
echo.
echo Database Connection Details:
echo   User Service:     postgresql://%DB_USER%:****@%DB_HOST%:%DB_PORT%/%USER_DB%
echo   Resume Service:   postgresql://%DB_USER%:****@%DB_HOST%:%DB_PORT%/%RESUME_DB%
echo   AI Service:       postgresql://%DB_USER%:****@%DB_HOST%:%DB_PORT%/%AI_DB%
echo.
echo Next Steps:
echo   1. Update your service configuration files with the database URLs
echo   2. Start your microservices
echo   3. Run the verification script: %0 --verify-only
echo.

exit /b 0

:check_postgres
echo [INFO] Checking PostgreSQL connection...
set "PGPASSWORD=%DB_PASSWORD%"
psql -h "%DB_HOST%" -p "%DB_PORT%" -U "%DB_USER%" -d postgres -c "SELECT 1;" >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] PostgreSQL connection successful
    exit /b 0
) else (
    echo [ERROR] Cannot connect to PostgreSQL. Please check your connection settings.
    echo [ERROR] Host: %DB_HOST%, Port: %DB_PORT%, User: %DB_USER%
    exit /b 1
)

:create_database
echo [INFO] Creating database: %1
set "PGPASSWORD=%DB_PASSWORD%"
psql -h "%DB_HOST%" -p "%DB_PORT%" -U "%DB_USER%" -d postgres -c "CREATE DATABASE \"%1\";" >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Database '%1' created successfully
) else (
    echo [WARNING] Database '%1' might already exist or creation failed
)
exit /b 0

:run_migrations
echo [INFO] Running migrations for %1...
if not exist "%3" (
    echo [ERROR] Migration directory not found: %3
    exit /b 1
)

for %%f in ("%3\*.sql") do (
    echo [INFO] Running migration: %%~nxf
    set "PGPASSWORD=%DB_PASSWORD%"
    psql -h "%DB_HOST%" -p "%DB_PORT%" -U "%DB_USER%" -d "%2" -f "%%f" >nul 2>&1
    if !errorlevel! equ 0 (
        echo [SUCCESS] Migration %%~nxf completed successfully
    ) else (
        echo [ERROR] Migration %%~nxf failed
        exit /b 1
    )
)

echo [SUCCESS] All migrations for %1 completed successfully
exit /b 0

:verify_setup
echo [INFO] Verifying database setup...

REM Check if databases exist
for %%db in ("%USER_DB%" "%RESUME_DB%" "%AI_DB%") do (
    set "PGPASSWORD=%DB_PASSWORD%"
    psql -h "%DB_HOST%" -p "%DB_PORT%" -U "%DB_USER%" -d "%%~db" -c "SELECT 1;" >nul 2>&1
    if !errorlevel! equ 0 (
        echo [SUCCESS] Database '%%~db' is accessible
    ) else (
        echo [ERROR] Database '%%~db' is not accessible
        exit /b 1
    )
)

echo [INFO] Checking key tables...

REM User service tables
set "PGPASSWORD=%DB_PASSWORD%"
psql -h "%DB_HOST%" -p "%DB_PORT%" -U "%DB_USER%" -d "%USER_DB%" -c "SELECT COUNT(*) FROM users;" >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] User service tables created successfully
) else (
    echo [ERROR] User service tables not found
    exit /b 1
)

REM Resume service tables
set "PGPASSWORD=%DB_PASSWORD%"
psql -h "%DB_HOST%" -p "%DB_PORT%" -U "%DB_USER%" -d "%RESUME_DB%" -c "SELECT COUNT(*) FROM resumes;" >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Resume service tables created successfully
) else (
    echo [ERROR] Resume service tables not found
    exit /b 1
)

REM AI service tables
set "PGPASSWORD=%DB_PASSWORD%"
psql -h "%DB_HOST%" -p "%DB_PORT%" -U "%DB_USER%" -d "%AI_DB%" -c "SELECT COUNT(*) FROM ai_processing_sessions;" >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] AI service tables created successfully
) else (
    echo [ERROR] AI service tables not found
    exit /b 1
)

echo [SUCCESS] Database setup verification completed successfully
exit /b 0

:show_usage
echo Usage: %0 [OPTIONS]
echo.
echo Options:
echo   --user-only           Setup only user service database
echo   --resume-only         Setup only resume service database
echo   --ai-only             Setup only AI service database
echo   --verify-only         Only verify existing setup
echo   --help                Show this help message
echo.
echo Environment Variables:
echo   DB_HOST               PostgreSQL host ^(default: localhost^)
echo   DB_PORT               PostgreSQL port ^(default: 5432^)
echo   DB_USER               PostgreSQL user ^(default: postgres^)
echo   DB_PASSWORD           PostgreSQL password
echo.
echo Examples:
echo   %0                                    # Setup all databases with defaults
echo   %0 --user-only                       # Setup only user service
echo   %0 --verify-only                     # Verify existing setup
echo.
exit /b 0

